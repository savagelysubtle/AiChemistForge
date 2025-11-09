use std::path::Path;

use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadMultipleFilesTool {
    pub paths: Vec<String>,
}

impl ReadMultipleFilesTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let mut results = Vec::new();
        for path in self.paths {
            match fs_service.read_file(Path::new(&path)).await {
                Ok(content) => results.push(format!("=== {} ===\n{}", path, content)),
                Err(e) => results.push(format!("=== {} ===\nError: {}", path, e)),
            }
        }

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: results.join("\n\n"),
            })],
            is_error: Some(false),
        })
    }
}
