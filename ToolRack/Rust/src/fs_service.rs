pub mod file_info;
pub mod utils;

use file_info::FileInfo;

use std::{
    env,
    path::{Path, PathBuf},
};

use similar::TextDiff;
use tokio::fs;
use utils::{
    expand_home, normalize_line_endings, normalize_path,
};
use walkdir::WalkDir;

use crate::{
    error::{ServiceError, ServiceResult},
    tools::EditOperation,
};

pub struct FileSystemService {
    allowed_path: Vec<PathBuf>,
    blocked_path: Vec<PathBuf>,
}

impl FileSystemService {
    pub fn try_new(allowed_directories: &[String], blocked_directories: &[String]) -> ServiceResult<Self> {
        let normalized_allowed_dirs: Vec<PathBuf> = if allowed_directories.is_empty() {
            // If no allowed directories specified, allow all (unrestricted mode)
            vec![]
        } else {
            allowed_directories
                .iter()
                .map(|dir| expand_home(dir.into()))
                .collect()
        };

        let normalized_blocked_dirs: Vec<PathBuf> = blocked_directories
            .iter()
            .map(|dir| expand_home(dir.into()))
            .collect();

        Ok(Self {
            allowed_path: normalized_allowed_dirs,
            blocked_path: normalized_blocked_dirs,
        })
    }

    pub fn allowed_directories(&self) -> &Vec<PathBuf> {
        &self.allowed_path
    }

    pub fn blocked_directories(&self) -> &Vec<PathBuf> {
        &self.blocked_path
    }
}

impl FileSystemService {
    pub async fn validate_path(&self, requested_path: &Path) -> ServiceResult<PathBuf> {
        // Expand ~ to home directory
        let expanded_path = expand_home(requested_path.to_path_buf());

        // Resolve the absolute path
        let absolute_path = if expanded_path.as_path().is_absolute() {
            expanded_path.clone()
        } else {
            env::current_dir().unwrap().join(&expanded_path)
        };

        // Normalize the path
        let normalized_requested = normalize_path(&absolute_path);

        // Check if path is in blocked directories first
        if !self.blocked_path.is_empty() {
            for blocked_dir in &self.blocked_path {
                if normalized_requested.starts_with(blocked_dir)
                    || normalized_requested.starts_with(&normalize_path(blocked_dir)) {
                    return Err(ServiceError::PathNotAllowed);
                }
            }
        }

        // If allowed_directories is empty, allow access (unrestricted mode)
        if self.allowed_path.is_empty() {
            return Ok(absolute_path);
        }

        // Otherwise, check allowlist as before
        if !self.allowed_path.iter().any(|dir| {
            normalized_requested.starts_with(dir)
                || normalized_requested.starts_with(&normalize_path(dir))
        }) {
            return Err(ServiceError::PathNotAllowed);
        }

        Ok(absolute_path)
    }

    // Separate validation for paths that must exist
    pub async fn validate_existing_path(&self, requested_path: &Path) -> ServiceResult<PathBuf> {
        let path = self.validate_path(requested_path).await?;

        if !path.exists() {
            return Err(ServiceError::FileNotFound(path.display().to_string()));
        }

        Ok(path)
    }

    // Get file stats
    pub async fn get_file_stats(&self, file_path: &Path) -> ServiceResult<FileInfo> {
        let valid_path = self.validate_existing_path(file_path).await?;

        match fs::metadata(&valid_path).await {
            Ok(metadata) => {
                let size = metadata.len();
                let created = metadata.created().ok();
                let modified = metadata.modified().ok();
                let accessed = metadata.accessed().ok();
                let is_directory = metadata.is_dir();
                let is_file = metadata.is_file();

                Ok(FileInfo {
                    size,
                    created,
                    modified,
                    accessed,
                    is_directory,
                    is_file,
                    metadata,
                })
            },
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    fn detect_line_ending(&self, text: &str) -> &str {
        if text.contains("\r\n") {
            "\r\n"
        } else if text.contains('\r') {
            "\r"
        } else {
            "\n"
        }
    }

    pub async fn read_file(&self, file_path: &Path) -> ServiceResult<String> {
        let valid_path = self.validate_existing_path(file_path).await?;

        match tokio::fs::read_to_string(valid_path).await {
            Ok(content) => Ok(content),
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    pub async fn create_directory(&self, file_path: &Path) -> ServiceResult<()> {
        let valid_path = self.validate_path(file_path).await?;

        // Check if directory already exists
        if valid_path.exists() && valid_path.is_dir() {
            return Err(ServiceError::DirectoryAlreadyExists);
        }

        match tokio::fs::create_dir_all(&valid_path).await {
            Ok(_) => Ok(()),
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    pub async fn move_file(&self, src_path: &Path, dest_path: &Path) -> ServiceResult<()> {
        let valid_src_path = self.validate_existing_path(src_path).await?;
        let valid_dest_path = self.validate_path(dest_path).await?;

        match tokio::fs::rename(&valid_src_path, &valid_dest_path).await {
            Ok(_) => Ok(()),
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    pub async fn list_directory(&self, dir_path: &Path) -> ServiceResult<Vec<tokio::fs::DirEntry>> {
        let valid_path = self.validate_existing_path(dir_path).await?;

        match tokio::fs::read_dir(valid_path).await {
            Ok(mut dir) => {
                let mut entries = Vec::new();
                while let Some(entry) = dir.next_entry().await? {
                    entries.push(entry);
                }
                Ok(entries)
            },
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    pub async fn write_file(&self, file_path: &Path, content: &String) -> ServiceResult<()> {
        let valid_path = self.validate_path(file_path).await?;

        match tokio::fs::write(&valid_path, content).await {
            Ok(_) => Ok(()),
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    pub async fn search_files(&self, directory: &Path, pattern: &str, include_content: bool) -> Result<Vec<String>, Box<dyn std::error::Error + Send + Sync>> {
        let valid_path = self.validate_existing_path(directory).await?;
        let mut results = Vec::new();
        let pattern_lower = pattern.to_lowercase();

        fn search_recursive(
            dir: &Path,
            pattern: &str,
            include_content: bool,
            results: &mut Vec<String>,
        ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
            for entry in std::fs::read_dir(dir)? {
                let entry = entry?;
                let path = entry.path();

                if path.is_dir() {
                    // Recursively search subdirectories
                    search_recursive(&path, pattern, include_content, results)?;
                } else if path.is_file() {
                    let file_name = path.file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("")
                        .to_lowercase();

                    let mut matches = false;

                    // Check filename match
                    if file_name.contains(pattern) {
                        matches = true;
                    }

                    // Check content match if requested
                    if include_content && !matches {
                        if let Ok(content) = std::fs::read_to_string(&path) {
                            if content.to_lowercase().contains(pattern) {
                                matches = true;
                            }
                        }
                    }

                    if matches {
                        results.push(path.to_string_lossy().to_string());
                    }
                }
            }
            Ok(())
        }

        search_recursive(&valid_path, &pattern_lower, include_content, &mut results)?;
        Ok(results)
    }

    pub fn create_unified_diff(
        &self,
        original_content: &str,
        new_content: &str,
        filepath: Option<String>,
    ) -> String {
        // Ensure consistent line endings for diff
        let normalized_original = normalize_line_endings(original_content);
        let normalized_new = normalize_line_endings(new_content);

        // // Generate the diff using TextDiff
        let diff = TextDiff::from_lines(&normalized_original, &normalized_new);

        let file_name = filepath.unwrap_or("file".to_string());
        // Format the diff as a unified diff
        let patch = diff
            .unified_diff()
            .header(
                format!("{}\toriginal", file_name).as_str(),
                format!("{}\tmodified", file_name).as_str(),
            )
            .context_radius(4)
            .to_string();

        format!("Index: {}\n{}\n{}", file_name, "=".repeat(68), patch)
    }

    pub async fn apply_file_edits(
        &self,
        file_path: &Path,
        edits: Vec<EditOperation>,
        dry_run: Option<bool>,
        save_to: Option<&Path>,
    ) -> ServiceResult<String> {
        let valid_path = self.validate_existing_path(file_path).await?;

        // Read file content and normalize line endings
        let content_str = tokio::fs::read_to_string(&valid_path).await?;
        let original_line_ending = self.detect_line_ending(&content_str);
        let content_str = normalize_line_endings(&content_str);

        // Apply edits sequentially
        let mut modified_content = content_str.clone();

        for edit in edits {
            let normalized_old = normalize_line_endings(&edit.old_text);
            let normalized_new = normalize_line_endings(&edit.new_text);

            // Apply simple string replacement
            if modified_content.contains(&normalized_old) {
                modified_content = modified_content.replacen(&normalized_old, &normalized_new, 1);
            }
        }

        let diff = self.create_unified_diff(
            &content_str,
            &modified_content,
            Some(valid_path.display().to_string()),
        );

        // Format diff with appropriate number of backticks
        let mut num_backticks = 3;
        while diff.contains(&"`".repeat(num_backticks)) {
            num_backticks += 1;
        }
        let formatted_diff = format!(
            "{}diff\n{}{}\n\n",
            "`".repeat(num_backticks),
            diff,
            "`".repeat(num_backticks)
        );

        let is_dry_run = dry_run.unwrap_or(false);

        if !is_dry_run {
            let target_path = if let Some(save_to) = save_to {
                self.validate_path(save_to).await?
            } else {
                valid_path
            };
            let modified_content = modified_content.replace("\n", original_line_ending);

            match tokio::fs::write(&target_path, modified_content).await {
                Ok(_) => {},
                Err(e) => {
                    match e.kind() {
                        std::io::ErrorKind::PermissionDenied => return Err(ServiceError::PermissionDenied),
                        _ => return Err(ServiceError::Io(e)),
                    }
                }
            }
        }

        Ok(formatted_diff)
    }

    pub async fn generate_directory_tree(&self, path: &Path, include_hidden: bool, max_depth: u32) -> ServiceResult<String> {
        let valid_path = self.validate_existing_path(path).await?;

        let mut tree_lines = Vec::new();
        tree_lines.push(format!("{}/", valid_path.file_name().unwrap_or_default().to_string_lossy()));

        let walker = if max_depth > 0 {
            WalkDir::new(&valid_path).max_depth(max_depth as usize)
        } else {
            WalkDir::new(&valid_path)
        };

        for entry in walker.into_iter().filter_map(|e| e.ok()) {
            if entry.path() == valid_path {
                continue;
            }

            let file_name = entry.file_name().to_string_lossy();

            // Skip hidden files if not requested
            if !include_hidden && file_name.starts_with('.') {
                continue;
            }

            let depth = entry.depth();
            let indent = "  ".repeat(depth);

            if entry.file_type().is_dir() {
                tree_lines.push(format!("{}├── {}/", indent, file_name));
            } else {
                tree_lines.push(format!("{}├── {}", indent, file_name));
            }
        }

        Ok(tree_lines.join("\n"))
    }

    pub async fn copy_file(&self, src_path: &Path, dest_path: &Path) -> ServiceResult<()> {
        let valid_src_path = self.validate_existing_path(src_path).await?;
        let valid_dest_path = self.validate_path(dest_path).await?;

        if valid_src_path.is_dir() {
            // For directories, use recursive copy
            self.copy_dir_recursive(&valid_src_path, &valid_dest_path).await?;
        } else {
            // For files, use simple copy
            tokio::fs::copy(&valid_src_path, &valid_dest_path).await?;
        }

        Ok(())
    }

    async fn copy_dir_recursive(&self, src: &Path, dest: &Path) -> ServiceResult<()> {
        tokio::fs::create_dir_all(dest).await?;

        let mut entries = tokio::fs::read_dir(src).await?;
        while let Some(entry) = entries.next_entry().await? {
            let src_path = entry.path();
            let dest_path = dest.join(entry.file_name());

            if src_path.is_dir() {
                Box::pin(self.copy_dir_recursive(&src_path, &dest_path)).await?;
            } else {
                tokio::fs::copy(&src_path, &dest_path).await?;
            }
        }

        Ok(())
    }

    pub async fn delete_file(&self, file_path: &Path) -> ServiceResult<()> {
        let valid_path = self.validate_existing_path(file_path).await?;

        match if valid_path.is_dir() {
            tokio::fs::remove_dir_all(&valid_path).await
        } else {
            tokio::fs::remove_file(&valid_path).await
        } {
            Ok(_) => Ok(()),
            Err(e) => {
                match e.kind() {
                    std::io::ErrorKind::PermissionDenied => Err(ServiceError::PermissionDenied),
                    _ => Err(ServiceError::Io(e)),
                }
            }
        }
    }

    // Add these new methods to the impl FileSystemService block
    pub async fn calculate_directory_size(&self, root_path: &Path) -> ServiceResult<u64> {
        let valid_path = self.validate_existing_path(root_path).await?;

        let mut total_size = 0;
        let mut entries = fs::read_dir(&valid_path).await?;
        while let Some(entry) = entries.next_entry().await? {
            let path = entry.path();
            if path.is_dir() {
                total_size += Box::pin(self.calculate_directory_size(&path)).await?;
            } else {
                total_size += entry.metadata().await?.len();
            }
        }
        Ok(total_size)
    }

    pub async fn find_duplicate_files(
        &self,
        _root_path: &Path,
        _pattern: Option<String>,
        _exclude_patterns: Option<Vec<String>>,
        _min_bytes: Option<u64>,
        _max_bytes: Option<u64>,
    ) -> ServiceResult<Vec<Vec<String>>> {
        // Placeholder implementation
        Ok(vec![])
    }

    pub async fn find_empty_directories(
        &self,
        _path: &Path,
        _exclude_patterns: Option<Vec<String>>,
    ) -> ServiceResult<Vec<String>> {
        // Placeholder implementation
        Ok(vec![])
    }

    pub async fn head_file(&self, path: &Path, lines: usize) -> ServiceResult<String> {
        let content = self.read_file(path).await?;
        Ok(content.lines().take(lines).collect::<Vec<_>>().join("\n"))
    }

    pub async fn tail_file(&self, path: &Path, lines: usize) -> ServiceResult<String> {
        let content = self.read_file(path).await?;
        let line_count = content.lines().count();
        Ok(content.lines().skip(line_count.saturating_sub(lines)).collect::<Vec<_>>().join("\n"))
    }

    pub async fn read_file_lines(
        &self,
        path: &Path,
        offset: usize,
        limit: Option<usize>,
    ) -> ServiceResult<String> {
        let content = self.read_file(path).await?;
        let lines = content.lines().skip(offset);
        match limit {
            Some(l) => Ok(lines.take(l).collect::<Vec<_>>().join("\n")),
            None => Ok(lines.collect::<Vec<_>>().join("\n")),
        }
    }

    pub async fn read_media_file(
        &self,
        path: &Path,
        _max_bytes: Option<usize>,
    ) -> ServiceResult<(infer::Type, String)> {
        let data = tokio::fs::read(path).await?;
        if let Some(kind) = infer::get(&data) {
            Ok((kind, base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &data)))
        } else {
            Err(ServiceError::InvalidMediaFile("unknown".to_string()))
        }
    }

    pub async fn read_media_files(
        &self,
        paths: Vec<String>,
        max_bytes: Option<usize>,
    ) -> ServiceResult<Vec<(infer::Type, String)>> {
        let mut results = Vec::new();
        for path_str in paths {
            let path = Path::new(&path_str);
            if let Ok(result) = self.read_media_file(path, max_bytes).await {
                results.push(result);
            }
        }
        Ok(results)
    }

    pub async fn search_files_content(
        &self,
        _path: &str,
        _pattern: &str,
        _query: &str,
        _is_regex: bool,
        _exclude_patterns: Option<Vec<String>>,
        _min_bytes: Option<u64>,
        _max_bytes: Option<u64>,
    ) -> ServiceResult<Vec<FileSearchResult>> {
        // Placeholder implementation
        Ok(vec![])
    }
}

// Add the FileSearchResult and Match structs
#[derive(Debug)]
pub struct FileSearchResult {
    pub file_path: PathBuf,
    pub matches: Vec<Match>,
}

#[derive(Debug)]
pub struct Match {
    pub line_number: usize,
    pub start_pos: usize,
    pub line_text: String,
}