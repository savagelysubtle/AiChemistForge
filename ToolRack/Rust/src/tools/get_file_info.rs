use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::fs_service::utils::{format_bytes, format_system_time, format_permissions};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GetFileInfoTool {
    pub path: String,
}

impl GetFileInfoTool {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        match fs_service.get_file_stats(Path::new(&self.path)).await {
            Ok(file_info) => {
                let mut info_text = format!("File Information for: {}\n", self.path);
                info_text.push_str(&format!("Type: {}\n", if file_info.is_directory { "Directory" } else { "File" }));
                info_text.push_str(&format!("Size: {} ({})\n", format_bytes(file_info.size), file_info.size));
                info_text.push_str(&format!("Permissions: {}\n", format_permissions(&file_info.metadata)));

                if let Some(created) = file_info.created {
                    info_text.push_str(&format!("Created: {}\n", format_system_time(created)));
                }
                if let Some(modified) = file_info.modified {
                    info_text.push_str(&format!("Modified: {}\n", format_system_time(modified)));
                }
                if let Some(accessed) = file_info.accessed {
                    info_text.push_str(&format!("Accessed: {}\n", format_system_time(accessed)));
                }

                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: info_text,
                    })],
                    is_error: Some(false),
                })
            },
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
