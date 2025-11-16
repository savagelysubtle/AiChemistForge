use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::retry::retry_3x;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadFileTool {
    pub path: String,
}

impl ReadFileTool {


    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        // Retry up to 3 times on transient I/O errors
        let path = self.path.clone();
        match retry_3x("read_file", || {
            let p = path.clone();
            async move {
                fs_service.read_file(Path::new(&p)).await
            }
        }).await {
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