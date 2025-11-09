use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::*;
use crate::task_state::{get_current_mode, add_workflow_step};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DirectoryOperationsTool {
    pub operation: String,
    pub path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub include_hidden: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_depth: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exclude_patterns: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_format: Option<String>,
}

impl DirectoryOperationsTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "directory_operations".to_string(),
            description: Some("Perform various directory operations including create, list, tree view, size calculation, and finding empty directories.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["create_directory", "list_directory", "directory_tree", "list_directory_with_sizes", "calculate_directory_size", "find_empty_directories"]
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory path to operate on"
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files in tree view",
                        "default": false
                    },
                    "max_depth": {
                        "type": "number",
                        "description": "Maximum depth for tree view"
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Patterns to exclude from empty directory search"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format for size calculation",
                        "enum": ["human-readable", "bytes"]
                    }
                },
                "required": ["operation", "path"]
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
                    text: format!("Operation '{}' is not available in the current operation mode. Use 'start_operation_mode' with 'directory_operations' to enable this operation.", self.operation),
                })],
                is_error: Some(true),
            });
        }

        let result = match self.operation.as_str() {
            "create_directory" => {
                let tool = CreateDirectoryTool { path: self.path.clone() };
                tool.run_tool(fs_service).await
            },
            "list_directory" => {
                let tool = ListDirectoryTool {
                    path: self.path.clone(),
                    detailed: Some(true),
                };
                tool.run_tool(fs_service).await
            },
            "directory_tree" => {
                let tool = DirectoryTreeTool {
                    path: self.path.clone(),
                    include_hidden: self.include_hidden.unwrap_or(false),
                    max_depth: self.max_depth.unwrap_or(0),
                };
                tool.run_tool(fs_service).await
            },
            "list_directory_with_sizes" => {
                let tool = ListDirectoryWithSizes { path: self.path.clone() };
                tool.run_tool(fs_service).await
            },
            "calculate_directory_size" => {
                let tool = CalculateDirectorySize {
                    root_path: self.path.clone(),
                    output_format: self.output_format,
                };
                tool.run_tool(fs_service).await
            },
            "find_empty_directories" => {
                let tool = FindEmptyDirectories {
                    path: self.path.clone(),
                    exclude_patterns: self.exclude_patterns.clone(),
                    output_format: Some("text".to_string()),
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
                    format!("directory_operations:{}", self.operation),
                    result_json,
                    None
                );
            }
        }

        result
    }
}
