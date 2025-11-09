use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CopyFileTool {
    pub source: String,
    pub destination: String,
}

impl CopyFileTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        match fs_service.copy_file(Path::new(&self.source), Path::new(&self.destination)).await {
            Ok(_) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Successfully copied {} to {}", self.source, self.destination),
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}