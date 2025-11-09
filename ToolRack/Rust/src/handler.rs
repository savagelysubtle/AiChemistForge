use std::collections::HashMap;
use serde_json::json;

use crate::{error::ServiceResult, fs_service::FileSystemService, cli::CommandArguments};
use crate::tools::{FileSystemTools, *};
use crate::tools::operation_mode_management::*;
use crate::mcp_types::*;

pub struct MyServerHandler {
    fs_service: FileSystemService,
}

impl MyServerHandler {
    pub fn new(args: &CommandArguments) -> ServiceResult<Self> {
        let fs_service = FileSystemService::try_new(&args.allowed_directories, &args.blocked_directories)?;
        Ok(Self {
            fs_service,
        })
    }

    pub fn assert_write_access(&self) -> std::result::Result<(), CallToolError> {
        // Always allow write access since we're in read-write mode
        Ok(())
    }

    pub fn startup_message(&self) -> String {
        format!(
            "Secure MCP Filesystem Server running in \"read/write\" mode.\nSecurity model: Allow all except blocked directories.\nAllowed directories: {}\nBlocked directories: {}",
            if self.fs_service.allowed_directories().is_empty() {
                "ALL (unrestricted)".to_string()
            } else {
                self.fs_service
                    .allowed_directories()
                    .iter()
                    .map(|p| p.display().to_string())
                    .collect::<Vec<String>>()
                    .join(",\n")
            },
            if self.fs_service.blocked_directories().is_empty() {
                "NONE".to_string()
            } else {
                self.fs_service
                    .blocked_directories()
                    .iter()
                    .map(|p| p.display().to_string())
                    .collect::<Vec<String>>()
                    .join(",\n")
            }
        )
    }

    pub async fn handle_list_tools(&self) -> Result<ListToolsResult, RpcError> {
        Ok(ListToolsResult {
            tools: FileSystemTools::tools(),
            meta: None,
            next_cursor: None,
        })
    }

    pub async fn handle_initialize(&self, _request: InitializeRequest) -> Result<InitializeResult, RpcError> {
        let mut capabilities = HashMap::new();
        capabilities.insert("tools".to_string(), json!({}));

        Ok(InitializeResult {
            protocol_version: "2024-11-05".to_string(),
            capabilities,
            server_info: ServerInfo {
                name: "aichemistforge-mcp-server".to_string(),
                version: "0.1.0".to_string(),
            },
        })
    }

    pub async fn handle_call_tool(&self, request: CallToolRequest) -> Result<CallToolResult, CallToolError> {
        let tool_params: FileSystemTools =
            FileSystemTools::try_from(request.params).map_err(CallToolError::new)?;

        // Verify write access for tools that modify the file system
        // Use tool-specific write access checking for better security
        if tool_params.require_write_access() {
            self.assert_write_access()?;
        }

        match tool_params {
            FileSystemTools::SingleFileOperationsTool(params) => {
                SingleFileOperationsTool::run_tool(params, &self.fs_service).await
            }
            FileSystemTools::MultipleFileOperationsTool(params) => {
                MultipleFileOperationsTool::run_tool(params, &self.fs_service).await
            }
            FileSystemTools::DirectoryOperationsTool(params) => {
                DirectoryOperationsTool::run_tool(params, &self.fs_service).await
            }
            FileSystemTools::SearchAndAnalysisTool(params) => {
                SearchAndAnalysisTool::run_tool(params, &self.fs_service).await
            }
            FileSystemTools::FileManagementTool(params) => {
                FileManagementTool::run_tool(params, &self.fs_service).await
            }
            // Operation mode management tools
            FileSystemTools::StartOperationMode(params) => {
                StartOperationModeTool::run_tool(params).await
            }
            FileSystemTools::CompleteCurrentMode(params) => {
                CompleteCurrentModeTool::run_tool(params).await
            }
            FileSystemTools::ListAvailableModes(params) => {
                ListAvailableModesTool::run_tool(params).await
            }
            FileSystemTools::GetCurrentModeStatus(params) => {
                GetCurrentModeStatusTool::run_tool(params).await
            }
        }
    }
}