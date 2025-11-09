use crate::handler::MyServerHandler;
use crate::mcp_types::*;
use anyhow::Result;
use serde_json::{json, Value};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

// JSON-RPC error codes from the specification
const PARSE_ERROR: i32 = -32700;
const INVALID_REQUEST: i32 = -32600;
const METHOD_NOT_FOUND: i32 = -32601;
const INVALID_PARAMS: i32 = -32602;
const INTERNAL_ERROR: i32 = -32603;

pub struct McpServer {
    handler: MyServerHandler,
}

impl McpServer {
    pub fn new(handler: MyServerHandler) -> Self {
        Self { handler }
    }

    pub async fn run(&self) -> Result<()> {
        let stdin = tokio::io::stdin();
        let mut stdout = tokio::io::stdout();
        let mut reader = BufReader::new(stdin);
        let mut line = String::new();

        eprintln!("MCP Server listening on stdin/stdout...");

        loop {
            line.clear();
            match reader.read_line(&mut line).await {
                Ok(0) => break, // EOF
                Ok(_) => {
                    let trimmed = line.trim();
                    if trimmed.is_empty() {
                        continue;
                    }

                    match self.handle_message(trimmed).await {
                        Ok(Some(response)) => {
                            let response_str = serde_json::to_string(&response)?;
                            stdout.write_all(response_str.as_bytes()).await?;
                            stdout.write_all(b"\n").await?;
                            stdout.flush().await?;
                        }
                        Ok(None) => {
                            // No response needed (notification)
                        }
                        Err(e) => {
                            eprintln!("Error handling message: {}", e);
                            // Try to extract ID from the original message for proper error response
                            let request_id = self.extract_request_id(trimmed);
                            let error_response = json!({
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": INTERNAL_ERROR,
                                    "message": e.to_string()
                                },
                                "id": request_id
                            });
                            let error_str = serde_json::to_string(&error_response)?;
                            stdout.write_all(error_str.as_bytes()).await?;
                            stdout.write_all(b"\n").await?;
                            stdout.flush().await?;
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error reading from stdin: {}", e);
                    break;
                }
            }
        }

        Ok(())
    }

    async fn handle_message(&self, message: &str) -> Result<Option<Value>> {
        // Debug: Log incoming message
        eprintln!("DEBUG: Received message: {}", message);

        // First, try to extract just the ID in case parsing fails
        let request_id = self.extract_request_id(message);

        let request: Value = match serde_json::from_str(message) {
            Ok(req) => req,
            Err(_) => {
                // Parse error - return with extracted ID or null
                return Ok(Some(json!({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": PARSE_ERROR,
                        "message": "Parse error"
                    },
                    "id": request_id
                })));
            }
        };

        let method = request["method"].as_str();
        let id = request.get("id").cloned();

        // Validate basic request structure
        if method.is_none() {
            return Ok(Some(json!({
                "jsonrpc": "2.0",
                "error": {
                    "code": INVALID_REQUEST,
                    "message": "Invalid Request - missing method"
                },
                "id": id
            })));
        }

        let method = method.unwrap();

        match method {
            "initialize" => {
                let params = request.get("params").cloned().unwrap_or(json!({}));
                match serde_json::from_value::<InitializeParams>(params) {
                    Ok(params) => {
                        let init_request = InitializeRequest { params };
                        match self.handler.handle_initialize(init_request).await {
                            Ok(result) => {
                                let response = json!({
                                    "jsonrpc": "2.0",
                                    "result": result,
                                    "id": id
                                });
                                eprintln!("DEBUG: Sending response: {}", serde_json::to_string(&response).unwrap_or_default());
                                Ok(Some(response))
                            }
                            Err(e) => {
                                Ok(Some(json!({
                                    "jsonrpc": "2.0",
                                    "error": {
                                        "code": e.code,
                                        "message": e.message
                                    },
                                    "id": id
                                })))
                            }
                        }
                    }
                    Err(_) => {
                        Ok(Some(json!({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": INVALID_PARAMS,
                                "message": "Invalid params for initialize"
                            },
                            "id": id
                        })))
                    }
                }
            }
            "tools/list" => {
                eprintln!("DEBUG: Received tools/list request");
                match self.handler.handle_list_tools().await {
                    Ok(result) => {
                        let response = json!({
                            "jsonrpc": "2.0",
                            "result": result,
                            "id": id
                        });
                        eprintln!("DEBUG: Sending tools/list response: {}", serde_json::to_string(&response).unwrap_or_default());
                        Ok(Some(response))
                    }
                    Err(e) => {
                        Ok(Some(json!({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": e.code,
                                "message": e.message
                            },
                            "id": id
                        })))
                    }
                }
            }
            "tools/call" => {
                let params = request.get("params").cloned().unwrap_or(json!({}));
                match serde_json::from_value::<CallToolParams>(params) {
                    Ok(params) => {
                        let call_request = CallToolRequest { params };
                        match self.handler.handle_call_tool(call_request).await {
                            Ok(result) => {
                                Ok(Some(json!({
                                    "jsonrpc": "2.0",
                                    "result": result,
                                    "id": id
                                })))
                            }
                            Err(e) => {
                                Ok(Some(json!({
                                    "jsonrpc": "2.0",
                                    "error": {
                                        "code": INTERNAL_ERROR,
                                        "message": e.message
                                    },
                                    "id": id
                                })))
                            }
                        }
                    }
                    Err(_) => {
                        Ok(Some(json!({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": INVALID_PARAMS,
                                "message": "Invalid params for tools/call"
                            },
                            "id": id
                        })))
                    }
                }
            }
            "notifications/initialized" => {
                // Notification - no response needed
                eprintln!("{}", self.handler.startup_message());
                Ok(None)
            }
            "initialized" => {
                // Legacy notification format - no response needed
                eprintln!("{}", self.handler.startup_message());
                Ok(None)
            }
            _ => {
                // Only return error for requests that have IDs
                if id.is_some() {
                    Ok(Some(json!({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": METHOD_NOT_FOUND,
                            "message": format!("Method not found: {}", method)
                        },
                        "id": id
                    })))
                } else {
                    // Ignore unknown notifications
                    Ok(None)
                }
            }
        }
    }

    fn extract_request_id(&self, message: &str) -> Value {
        // Try to extract just the ID field, even if the rest fails to parse
        if let Ok(partial) = serde_json::from_str::<Value>(message) {
            if let Some(id) = partial.get("id") {
                return id.clone();
            }
        }
        Value::Null
    }
}
