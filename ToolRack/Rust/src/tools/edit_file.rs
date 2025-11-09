use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::EditOperation;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EditFileTool {
    pub path: String,
    pub edits: Vec<EditOperation>,
    #[serde(rename = "dryRun", default, skip_serializing_if = "std::option::Option::is_none")]
    pub dry_run: Option<bool>,
}

impl EditFileTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let is_dry_run = self.dry_run.unwrap_or(false);

        match fs_service.apply_file_edits(
            Path::new(&self.path),
            self.edits,
            Some(is_dry_run),
            None
        ).await {
            Ok(diff_output) => {
                let message = if is_dry_run {
                    format!("Preview of changes to {}:\n\n{}", self.path, diff_output)
                } else {
                    format!("Successfully edited file: {}\n\nChanges applied:\n{}", self.path, diff_output)
                };

                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: message,
                    })],
                    is_error: Some(false),
                })
            }
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
