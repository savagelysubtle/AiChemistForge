use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadFileLines {
    pub path: String,
    pub offset: u64,
    pub limit: Option<u64>,
}

impl ReadFileLines {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let result = fs_service
            .read_file_lines(
                Path::new(&self.path),
                self.offset as usize,
                self.limit.map(|v| v as usize),
            )
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
