use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoveFileTool {
    /// The **absolute source path** of the file or directory to be moved/renamed (e.g., `D:\\old_folder\\item.dat`).
    pub source: String,
    /// The **absolute destination path** for the file or directory (e.g., `D:\\new_location\\item_new_name.dat`). This path must not already exist.
    pub destination: String,
}

impl MoveFileTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        match fs_service.move_file(Path::new(&self.source), Path::new(&self.destination)).await {
            Ok(_) => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Successfully moved {} to {}", self.source, self.destination),
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
