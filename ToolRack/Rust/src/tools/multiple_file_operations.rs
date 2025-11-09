use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::*;
use crate::task_state::{get_current_mode, add_workflow_step};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultipleFileOperationsTool {
    pub operation: String,
    pub paths: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub destination: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pattern: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_bytes: Option<u64>,
}

impl MultipleFileOperationsTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "multiple_file_operations".to_string(),
            description: Some("Perform various operations on multiple files including read, copy, move, zip, unzip, and read media files.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["read_multiple_files", "read_multiple_media_files", "copy_files", "move_files", "zip_files", "unzip_file", "zip_directory"]
                    },
                    "paths": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Array of file paths to operate on"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination path for copy/move operations"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output path for zip operations"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Pattern for zip_directory operation"
                    },
                    "max_bytes": {
                        "type": "number",
                        "description": "Maximum file size in bytes for media files"
                    }
                },
                "required": ["operation", "paths"]
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
                    text: format!("Operation '{}' is not available in the current operation mode. Use 'start_operation_mode' with 'multiple_file_operations' to enable this operation.", self.operation),
                })],
                is_error: Some(true),
            });
        }

        let result = match self.operation.as_str() {
            "read_multiple_files" => {
                let tool = ReadMultipleFilesTool { paths: self.paths.clone() };
                tool.run_tool(fs_service).await
            },
            "read_multiple_media_files" => {
                let tool = ReadMultipleMediaFiles {
                    paths: self.paths.clone(),
                    max_bytes: self.max_bytes,
                };
                tool.run_tool(fs_service).await
            },
            "copy_files" => {
                if self.destination.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Destination is required for copy_files operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                // Copy each file to the destination directory
                let mut results = Vec::new();
                for path in &self.paths {
                    let dest_path = std::path::Path::new(&self.destination.as_ref().unwrap()).join(
                        std::path::Path::new(path).file_name().unwrap_or_default()
                    );
                    let tool = CopyFileTool {
                        source: path.clone(),
                        destination: dest_path.to_string_lossy().to_string(),
                    };
                    match tool.run_tool(fs_service).await {
                        Ok(_result) => results.push(format!("Copied {}: Success", path)),
                        Err(e) => results.push(format!("Copied {}: Error - {}", path, e.message)),
                    }
                }
                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: format!("Copy operation completed:\n{}", results.join("\n")),
                    })],
                    is_error: Some(false),
                })
            },
            "move_files" => {
                if self.destination.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Destination is required for move_files operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                // Move each file to the destination directory
                let mut results = Vec::new();
                for path in &self.paths {
                    let dest_path = std::path::Path::new(&self.destination.as_ref().unwrap()).join(
                        std::path::Path::new(path).file_name().unwrap_or_default()
                    );
                    let tool = MoveFileTool {
                        source: path.clone(),
                        destination: dest_path.to_string_lossy().to_string(),
                    };
                    match tool.run_tool(fs_service).await {
                        Ok(_result) => results.push(format!("Moved {}: Success", path)),
                        Err(e) => results.push(format!("Moved {}: Error - {}", path, e.message)),
                    }
                }
                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: format!("Move operation completed:\n{}", results.join("\n")),
                    })],
                    is_error: Some(false),
                })
            },
            "zip_files" => {
                if self.output_path.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Output path is required for zip_files operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = ZipFilesTool {
                    files: self.paths.clone(),
                    output_path: self.output_path.unwrap(),
                };
                tool.run_tool(fs_service).await
            },
            "unzip_file" => {
                if self.output_path.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Output path is required for unzip_file operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                // For simplicity, we'll assume the first path is the zip file
                if self.paths.is_empty() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "At least one zip file path is required".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = UnzipFileTool {
                    zip_path: self.paths[0].clone(),
                    output_dir: self.output_path.unwrap(),
                };
                tool.run_tool(fs_service).await
            },
            "zip_directory" => {
                if self.output_path.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Output path is required for zip_directory operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                // For simplicity, we'll assume the first path is the directory to zip
                if self.paths.is_empty() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "At least one directory path is required".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = ZipDirectoryTool {
                    directory_path: self.paths[0].clone(),
                    output_path: self.output_path.unwrap(),
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
                    "path_count": self.paths.len(),
                    "success": true
                });
                add_workflow_step(
                    format!("multiple_file_operations:{}", self.operation),
                    result_json,
                    None
                );
            }
        }

        result
    }
}
