use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::{FileSystemService, utils::format_bytes};
use std::fmt::Write;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListDirectoryWithSizes {
    pub path: String,
}

impl ListDirectoryWithSizes {
    

    async fn format_directory_entries(
        &self,
        mut entries: Vec<tokio::fs::DirEntry>,
    ) -> Result<String, String> {
        let mut file_count = 0;
        let mut dir_count = 0;
        let mut total_size: u64 = 0;
        // Estimate initial capacity: assume ~50 bytes per entry + summary
        let mut output = String::with_capacity(entries.len() * 50 + 120);
        // Sort entries by file name
        entries.sort_by_key(|a| a.file_name());
        // build the output string
        for entry in &entries {
            let file_name = entry.file_name();
            let file_name = file_name.to_string_lossy();
            if entry.path().is_dir() {
                writeln!(output, "[DIR]  {file_name:<30}").map_err(|e| e.to_string())?;
                dir_count += 1;
            } else if entry.path().is_file() {
                let metadata = entry.metadata().await.map_err(|e| e.to_string())?;
                let file_size = metadata.len();
                writeln!(
                    output,
                    "[FILE] {:<30} {:>10}",
                    file_name,
                    format_bytes(file_size)
                )
                .map_err(|e| e.to_string())?;
                file_count += 1;
                total_size += file_size;
            }
        }
        // Append summary
        writeln!(
            output,
            "\nTotal: {file_count} files, {dir_count} directories"
        )
        .map_err(|e| e.to_string())?;
        writeln!(output, "Total size: {}", format_bytes(total_size)).map_err(|e| e.to_string())?;
        Ok(output)
    }

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let entries = fs_service
            .list_directory(std::path::Path::new(&self.path))
            .await
            .map_err(CallToolError::new)?;

        let output = self
            .format_directory_entries(entries)
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: output,
            })],
            is_error: Some(false),
        })
    }
}
