use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::fmt::Write;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FindEmptyDirectories {
    pub path: String,
    pub exclude_patterns: Option<Vec<String>>,
    pub output_format: Option<String>,
}

impl FindEmptyDirectories {
    

    fn format_output(
        empty_dirs: Vec<String>,
        output_format: &str,
    ) -> Result<String, String> {
        match output_format {
            "json" => {
                Ok(serde_json::to_string_pretty(&empty_dirs).map_err(|e| e.to_string())?)
            }
            _ => {
                let mut output = String::new();
                let header = if empty_dirs.is_empty() {
                    "No empty directories were found.".to_string()
                } else {
                    format!(
                        "Found {} empty {}:\n",
                        empty_dirs.len(),
                        (if empty_dirs.len() == 1 {
                            "directory"
                        } else {
                            "directories"
                        }),
                    )
                };
                output.push_str(&header);
                for dir in empty_dirs {
                    writeln!(output, "  {dir}").map_err(|e| e.to_string())?;
                }
                Ok(output)
            }
        }
    }

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let result = fs_service
            .find_empty_directories(std::path::Path::new(&self.path), self.exclude_patterns)
            .await
            .map_err(CallToolError::new)?;

        let output_format = self.output_format.as_deref().unwrap_or("text");
        let content = Self::format_output(result, output_format)
            .map_err(CallToolError::new)?;

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: content,
            })],
            is_error: Some(false),
        })
    }
}
