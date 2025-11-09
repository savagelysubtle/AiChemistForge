use std::path::Path;
use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateDirectoryTool {
    pub path: String,
}

impl CreateDirectoryTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        match fs_service.create_directory(Path::new(&self.path)).await {
            Ok(_) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Successfully created directory: {}", self.path),
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
