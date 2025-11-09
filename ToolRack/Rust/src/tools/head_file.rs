use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeadFile {
    pub path: String,
    pub lines: u64,
}

impl HeadFile {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let result = fs_service
            .head_file(Path::new(&self.path), self.lines as usize)
            .await
            .map_err(CallToolError::new)?;

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: result,
            })],
            is_error: Some(false),
        })
    }
}
