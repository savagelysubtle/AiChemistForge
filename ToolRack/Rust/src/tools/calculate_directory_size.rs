use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::{FileSystemService, utils::format_bytes};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalculateDirectorySize {
    pub root_path: String,
    pub output_format: Option<String>,
}

impl CalculateDirectorySize {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let total_bytes = fs_service
            .calculate_directory_size(Path::new(&self.root_path))
            .await
            .map_err(CallToolError::new)?;
        let output_content = match self.output_format.as_deref().unwrap_or("human-readable") {
            "human-readable" => format_bytes(total_bytes),
            "bytes" => format!("{total_bytes}"),
            _ => format_bytes(total_bytes),
        };
        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: output_content,
            })],
            is_error: Some(false),
        })
    }
}
