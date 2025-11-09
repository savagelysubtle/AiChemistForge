use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use crate::tools::*;
use crate::task_state::{get_current_mode, add_workflow_step};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchAndAnalysisTool {
    pub operation: String,
    pub path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pattern: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub query: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_regex: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exclude_patterns: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub include_content: Option<bool>,
}

impl SearchAndAnalysisTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "search_and_analysis".to_string(),
            description: Some("Perform search and analysis operations including file search, content search, and finding duplicate files.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The operation to perform",
                        "enum": ["search_files", "search_files_content", "find_duplicate_files"]
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory path to search in"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "File pattern for search operations"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for content search"
                    },
                    "is_regex": {
                        "type": "boolean",
                        "description": "Whether query is a regex pattern",
                        "default": false
                    },
                    "exclude_patterns": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "Patterns to exclude from search"
                    },
                    "min_bytes": {
                        "type": "number",
                        "description": "Minimum file size for duplicate search"
                    },
                    "max_bytes": {
                        "type": "number",
                        "description": "Maximum file size for duplicate search"
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Include file content in search",
                        "default": false
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
                    text: format!("Operation '{}' is not available in the current operation mode. Use 'start_operation_mode' with 'search_and_analysis' to enable this operation.", self.operation),
                })],
                is_error: Some(true),
            });
        }

        let result = match self.operation.as_str() {
            "search_files" => {
                if self.pattern.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Pattern is required for search_files operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = SearchFilesTool {
                    directory: self.path.clone(),
                    pattern: self.pattern.unwrap(),
                    include_content: Some(self.include_content.unwrap_or(false)),
                };
                tool.run_tool(fs_service).await
            },
            "search_files_content" => {
                if self.pattern.is_none() || self.query.is_none() {
                    return Ok(CallToolResult {
                        content: vec![Content::Text(TextContent {
                            text: "Pattern and query are required for search_files_content operation".to_string(),
                        })],
                        is_error: Some(true),
                    });
                }
                let tool = SearchFilesContent {
                    path: self.path.clone(),
                    pattern: self.pattern.unwrap(),
                    query: self.query.unwrap(),
                    is_regex: self.is_regex,
                    exclude_patterns: self.exclude_patterns.clone(),
                    min_bytes: self.min_bytes,
                    max_bytes: self.max_bytes,
                };
                tool.run_tool(fs_service).await
            },
            "find_duplicate_files" => {
                let tool = FindDuplicateFiles {
                    root_path: self.path.clone(),
                    pattern: self.pattern.clone(),
                    exclude_patterns: self.exclude_patterns.clone(),
                    min_bytes: self.min_bytes,
                    max_bytes: self.max_bytes,
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
                    format!("search_and_analysis:{}", self.operation),
                    result_json,
                    None
                );
            }
        }

        result
    }
}
