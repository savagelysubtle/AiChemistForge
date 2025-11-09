use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::fs_service::utils::format_bytes;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListDirectoryTool {
    /// The **absolute path** of the directory whose contents are to be listed
    pub path: String,
    #[serde(default)]
    pub detailed: Option<bool>,
}

impl ListDirectoryTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let show_detailed = self.detailed.unwrap_or(false);

        match fs_service.list_directory(Path::new(&self.path)).await {
            Ok(entries) => {
                if entries.is_empty() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Directory is empty".to_string(),
                        })],
                        is_error: Some(false),
                    });
                }

                let mut output = Vec::new();

                for entry in entries {
                    let file_name = entry.file_name().to_string_lossy().to_string();

                    if show_detailed {
                        if let Ok(metadata) = entry.metadata().await {
                            let file_type = if metadata.is_dir() { "DIR " } else { "FILE" };
                            let size = if metadata.is_file() {
                                format!(" ({}) ", format_bytes(metadata.len()))
                            } else {
                                " ".to_string()
                            };
                            output.push(format!("{}{}{}", file_type, size, file_name));
                        } else {
                            output.push(format!("???? {}", file_name));
                        }
                    } else {
                        output.push(file_name);
                    }
                }

                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: output.join("\n"),
                    })],
                    is_error: Some(false),
                })
            },
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
