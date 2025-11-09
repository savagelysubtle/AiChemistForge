use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, CallToolError};
use crate::fs_service::FileSystemService;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListAllowedDirectoriesTool {}

impl ListAllowedDirectoriesTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let directories: Vec<String> = fs_service
            .allowed_directories()
            .iter()
            .map(|path| path.display().to_string())
            .collect();

        Ok(CallToolResult {
            content: vec![crate::mcp_types::Content::Text(crate::mcp_types::TextContent {
                text: directories.join("\n"),
            })],
            is_error: Some(false),
        })
    }
}
