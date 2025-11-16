use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::retry::retry_3x;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WriteFileTool {
    pub path: String,
    pub content: String,
}

impl WriteFileTool {


    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        // Retry up to 3 times on transient I/O errors
        let path = self.path.clone();
        let content = self.content.clone();
        match retry_3x("write_file", || {
            let p = path.clone();
            let c = content.clone();
            async move {
                fs_service.write_file(Path::new(&p), &c).await
            }
        }).await {
            Ok(_) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Successfully wrote to file: {}", self.path),
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
