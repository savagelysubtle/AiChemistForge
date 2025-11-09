use std::{
    fs::{self},
    path::{Path, PathBuf},
    time::SystemTime,
};

use chrono::{DateTime, Local};
use dirs::home_dir;

// Add this enum at the top of the file
#[derive(::serde::Deserialize, ::serde::Serialize, Clone, Debug)]
pub enum OutputFormat {
    #[serde(rename = "text")]
    Text,
    #[serde(rename = "json")]
    Json,
}

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

#[cfg(windows)]
use std::os::windows::fs::MetadataExt;

pub fn format_system_time(system_time: SystemTime) -> String {
    // Convert SystemTime to DateTime<Local>
    let datetime: DateTime<Local> = system_time.into();
    datetime.format("%a %b %d %Y %H:%M:%S %:z").to_string()
}

pub fn format_permissions(metadata: &fs::Metadata) -> String {
    #[cfg(unix)]
    {
        let permissions = metadata.permissions();
        let mode = permissions.mode();
        format!("0{:o}", mode & 0o777) // Octal representation
    }

    #[cfg(windows)]
    {
        let attributes = metadata.file_attributes();
        let read_only = (attributes & 0x1) != 0; // FILE_ATTRIBUTE_READONLY
        let directory = metadata.is_dir();

        let mut result = String::new();

        if directory {
            result.push('d');
        } else {
            result.push('-');
        }

        if read_only {
            result.push('r');
        } else {
            result.push('w');
        }

        result
    }
}

pub fn normalize_path(path: &Path) -> PathBuf {
    path.canonicalize().unwrap_or_else(|_| path.to_path_buf())
}

pub fn expand_home(path: PathBuf) -> PathBuf {
    if let Some(home_dir) = home_dir() {
        if path.starts_with("~") {
            let stripped_path = path.strip_prefix("~").unwrap_or(&path);
            return home_dir.join(stripped_path);
        }
    }
    path
}

pub fn format_bytes(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB", "TB", "PB"];

    if bytes == 0 {
        return "0 B".to_string();
    }

    let mut size = bytes as f64;
    let mut unit_index = 0;

    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }

    if unit_index == 0 {
        format!("{} {}", bytes, UNITS[unit_index])
    } else {
        format!("{:.1} {}", size, UNITS[unit_index])
    }
}

pub fn normalize_line_endings(content: &str) -> String {
    content.replace("\r\n", "\n").replace('\r', "\n")
}

// Remove unused zip and symlink functions for now
// TODO: Re-implement when needed


