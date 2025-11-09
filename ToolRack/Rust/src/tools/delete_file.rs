use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeleteFileTool {
    pub path: String,
    #[serde(default)]
    pub confirm: Option<bool>,
}

impl DeleteFileTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let confirmed = self.confirm.unwrap_or(false);

        if !confirmed {
            return Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: "Delete operation requires confirmation. Set 'confirm: true' to proceed.".to_string(),
                })],
                is_error: Some(true),
            });
        }

        match fs_service.delete_file(Path::new(&self.path)).await {
            Ok(_) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Successfully deleted: {}", self.path),
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}