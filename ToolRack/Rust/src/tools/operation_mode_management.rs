use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::mcp_types::{Tool, CallToolResult, Content, TextContent, CallToolError};
use crate::task_state::{get_current_mode, add_workflow_step, complete_current_mode, get_available_operation_modes, get_operation_mode_tools, start_operation_mode};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartOperationModeTool {
    pub mode_name: String,
}

impl StartOperationModeTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "start_operation_mode".to_string(),
            description: Some("Start a new operation mode that enables specific sets of file operations. Available modes: single_file_operations, multiple_file_operations, directory_operations, search_and_analysis, file_management.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {
                    "mode_name": {
                        "type": "string",
                        "description": "The operation mode to start",
                        "enum": ["single_file_operations", "multiple_file_operations", "directory_operations", "search_and_analysis", "file_management"]
                    }
                },
                "required": ["mode_name"]
            }),
        }
    }

    pub async fn run_tool(self) -> Result<CallToolResult, CallToolError> {
        let available_tools = get_operation_mode_tools(&self.mode_name);

        if available_tools.is_empty() {
            return Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: format!("Unknown operation mode: {}", self.mode_name),
                })],
                is_error: Some(true),
            });
        }

        let mode = start_operation_mode(self.mode_name.clone(), available_tools);

        let result_json = json!({
            "mode_started": self.mode_name,
            "available_tools": mode.available_tools,
            "start_time": mode.start_time.to_rfc3339()
        });

        add_workflow_step(
            "start_operation_mode".to_string(),
            result_json.clone(),
            None
        );

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: format!("Started operation mode '{}' with {} available tools: {}",
                    self.mode_name,
                    mode.available_tools.len(),
                    mode.available_tools.join(", ")
                ),
            })],
            is_error: Some(false),
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompleteCurrentModeTool;

impl CompleteCurrentModeTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "complete_current_mode".to_string(),
            description: Some("Complete the current operation mode and return to the default state where no specific tools are enabled.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {}
            }),
        }
    }

    pub async fn run_tool(self) -> Result<CallToolResult, CallToolError> {
        let completed_mode = complete_current_mode();

        match completed_mode {
            Some(mode) => {
                let result_json = json!({
                    "mode_completed": mode.name,
                    "duration_seconds": chrono::Utc::now().timestamp() - mode.start_time.timestamp(),
                    "steps_completed": mode.workflow_history.len()
                });

                add_workflow_step(
                    "complete_current_mode".to_string(),
                    result_json.clone(),
                    None
                );

                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: format!("Completed operation mode '{}' after {} steps and {:.1} seconds",
                            mode.name,
                            mode.workflow_history.len(),
                            (chrono::Utc::now().timestamp() - mode.start_time.timestamp()) as f64
                        ),
                    })],
                    is_error: Some(false),
                })
            },
            None => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: "No operation mode was active".to_string(),
                })],
                is_error: Some(false),
            }),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListAvailableModesTool;

impl ListAvailableModesTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "list_available_modes".to_string(),
            description: Some("List all available operation modes and their associated tools.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {}
            }),
        }
    }

    pub async fn run_tool(self) -> Result<CallToolResult, CallToolError> {
        let modes = get_available_operation_modes();
        let mut mode_details = Vec::new();

        for mode in modes {
            let tools = get_operation_mode_tools(&mode);
            mode_details.push(format!("{}: {} tools", mode, tools.join(", ")));
        }

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: format!("Available operation modes:\n\n{}", mode_details.join("\n")),
            })],
            is_error: Some(false),
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GetCurrentModeStatusTool;

impl GetCurrentModeStatusTool {
    pub fn tool_definition() -> Tool {
        Tool {
            name: "get_current_mode_status".to_string(),
            description: Some("Get the status of the current operation mode including available tools and workflow history.".to_string()),
            input_schema: serde_json::json!({
                "type": "object",
                "properties": {}
            }),
        }
    }

    pub async fn run_tool(self) -> Result<CallToolResult, CallToolError> {
        let current_mode = get_current_mode();

        match current_mode {
            Some(mode) => {
                let summary = mode.get_workflow_summary();

                let mut status_text = format!(
                    "Current operation mode: {}\nStarted: {}\nDuration: {} seconds\nAvailable tools: {}\nSteps completed: {}\n\nWorkflow history:\n",
                    summary["mode_name"].as_str().unwrap_or("unknown"),
                    summary["start_time"].as_str().unwrap_or("unknown"),
                    summary["duration_seconds"].as_u64().unwrap_or(0),
                    summary["available_tools"].as_array().unwrap_or(&vec![]).len(),
                    summary["steps_completed"].as_u64().unwrap_or(0)
                );

                if let Some(workflow_steps) = summary.get("workflow_steps") {
                    if let Some(steps) = workflow_steps.as_array() {
                        for (i, step) in steps.iter().enumerate() {
                            if let (Some(step_name), Some(timestamp)) = (
                                step.get("step").and_then(|s| s.as_str()),
                                step.get("timestamp").and_then(|s| s.as_str())
                            ) {
                                status_text.push_str(&format!("  {}. {} - {}\n", i + 1, step_name, timestamp));
                            }
                        }
                    }
                } else {
                    status_text.push_str("  No workflow steps yet\n");
                }

                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: status_text,
                    })],
                    is_error: Some(false),
                })
            },
            None => Ok(CallToolResult {
                content: vec![Content::Text(TextContent {
                    text: "No operation mode is currently active. Use 'start_operation_mode' to begin a new workflow.".to_string(),
                })],
                is_error: Some(false),
            }),
        }
    }
}
