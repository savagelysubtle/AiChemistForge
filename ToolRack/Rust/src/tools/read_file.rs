use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadFileTool {
    pub path: String,
}

impl ReadFileTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        match fs_service.read_file(Path::new(&self.path)).await {
            Ok(content) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: content,
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}