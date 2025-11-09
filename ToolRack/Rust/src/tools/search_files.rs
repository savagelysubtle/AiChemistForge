use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchFilesTool {
    pub directory: String,
    pub pattern: String,
    #[serde(default)]
    pub include_content: Option<bool>,
}

impl SearchFilesTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let include_content = self.include_content.unwrap_or(false);

        match fs_service.search_files(Path::new(&self.directory), &self.pattern, include_content).await {
            Ok(results) => {
                if results.is_empty() {
                    Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: format!("No files found matching pattern '{}' in directory '{}'", self.pattern, self.directory),
                        })],
                        is_error: Some(false),
                    })
                } else {
                    let mut output = format!("Found {} file(s) matching pattern '{}':\n\n", results.len(), self.pattern);
                    for (i, file_path) in results.iter().enumerate() {
                        output.push_str(&format!("{}. {}\n", i + 1, file_path));
                    }

                    Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: output,
                        })],
                        is_error: Some(false),
                    })
                }
            }
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}