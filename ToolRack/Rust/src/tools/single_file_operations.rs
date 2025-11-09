use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::*;
use crate::task_state::{get_current_mode, add_workflow_step};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SingleFileOperationsTool {
    pub operation: String,
    pub path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lines: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub offset: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub edits: Option<Vec<EditOperation>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dry_run: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_bytes: Option<u64>,
}

impl SingleFileOperationsTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "single_file_operations".to_string(),
            description: Some("Perform various operations on a single file including read, write, edit, get info, head, tail, read lines, and read media files.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["read_file", "write_file", "edit_file", "get_file_info", "head_file", "tail_file", "read_file_lines", "read_media_file"]
                    },
                    "path": {
                        "type": "string",
                        "description": "The path of the file to operate on"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (required for write_file operation)"
                    },
                    "lines": {
                        "type": "number",
                        "description": "Number of lines to read from head or tail (required for head_file and tail_file operations)"
                    },
                    "offset": {
                        "type": "number",
                        "description": "Line offset for read_file_lines operation"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of lines to read for read_file_lines operation"
                    },
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "oldText": {"type": "string", "description": "Text to replace"},
                                "newText": {"type": "string", "description": "Replacement text"}
                            },
                            "required": ["oldText", "newText"]
                        },
                        "description": "Array of edit operations for edit_file"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview changes without applying (for edit_file operation)",
                        "default": false
                    },
                    "max_bytes": {
                        "type": "number",
                        "description": "Maximum file size in bytes for media files"
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
                    text: format!("Operation '{}' is not available in the current operation mode. Use 'start_operation_mode' with 'single_file_operations' to enable this operation.", self.operation),
                })],
                is_error: Some(true),
            });
        }

        let result = match self.operation.as_str() {
            "read_file" => {
                let tool = ReadFileTool { path: self.path.clone() };
                tool.run_tool(fs_service).await
            },
            "write_file" => {
                if self.content.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Content is required for write_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = WriteFileTool { path: self.path.clone(), content: self.content.unwrap() };
                tool.run_tool(fs_service).await
            },
            "edit_file" => {
                if self.edits.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Edits array is required for edit_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = EditFileTool {
                    path: self.path.clone(),
                    edits: self.edits.unwrap(),
                    dry_run: self.dry_run,
                };
                tool.run_tool(fs_service).await
            },
            "get_file_info" => {
                let tool = GetFileInfoTool { path: self.path.clone() };
                tool.run_tool(fs_service).await
            },
            "head_file" => {
                if self.lines.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Lines parameter is required for head_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = HeadFile { path: self.path.clone(), lines: self.lines.unwrap() };
                tool.run_tool(fs_service).await
            },
            "tail_file" => {
                if self.lines.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Lines parameter is required for tail_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = TailFile { path: self.path.clone(), lines: self.lines.unwrap() };
                tool.run_tool(fs_service).await
            },
            "read_file_lines" => {
                if self.offset.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Offset parameter is required for read_file_lines operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = ReadFileLines {
                    path: self.path.clone(),
                    offset: self.offset.unwrap(),
                    limit: self.limit,
                };
                tool.run_tool(fs_service).await
            },
            "read_media_file" => {
                let tool = ReadMediaFile {
                    path: self.path.clone(),
                    max_bytes: self.max_bytes,
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
                    format!("single_file_operations:{}", self.operation),
                    result_json,
                    None
                );
            }
        }

        result
    }
}
