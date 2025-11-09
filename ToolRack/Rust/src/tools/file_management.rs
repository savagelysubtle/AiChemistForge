use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::*;
use crate::task_state::{get_current_mode, add_workflow_step};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileManagementTool {
    pub operation: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub confirm: Option<bool>,
}

impl FileManagementTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "file_management".to_string(),
            description: Some("Perform file management operations including listing allowed directories and deleting files.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["list_allowed_directories", "delete_file"]
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory path for delete operation"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation for delete operation",
                        "default": false
                    }
                },
                "required": ["operation"]
            }),
        }
    }

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let current_mode = get_current_mode();
        let available_tools = current_mode.as_ref().map(|m| m.available_tools.clone()).unwrap_or_default();

        // Check if the requested operation is available in current mode
        if !available_tools.contains(&self.operation) {
            return Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Operation '{}' is not available in the current operation mode. Use 'start_operation_mode' with 'file_management' to enable this operation.", self.operation),
                })],
                is_error: Some(true),
            });
        }

        let result = match self.operation.as_str() {
            "list_allowed_directories" => {
                let tool = ListAllowedDirectoriesTool {};
                tool.run_tool(fs_service).await
            },
            "delete_file" => {
                if self.path.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Path is required for delete_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = DeleteFileTool {
                    path: self.path.clone().unwrap(),
                    confirm: self.confirm,
                };
                tool.run_tool(fs_service).await
            },
            _ => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Unknown operation: {}", self.operation),
                })],
                is_error: Some(true),
            }),
        };

        // Add workflow step if operation was successful
        if let Ok(ref call_result) = result {
            if !call_result.is_error.unwrap_or(false) {
                let result_json = json!({
                    "operation": self.operation.clone(),
                    "path": self.path.clone(),
                    "success": true
                });
                add_workflow_step(
                    format!("file_management:{}", self.operation),
                    result_json,
                    None
                );
            }
        }

        result
    }
}
