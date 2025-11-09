use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Simple MCP types without external dependencies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tool {
    pub name: String,
    pub description: Option<String>,
    #[serde(rename = "inputSchema")]
    pub input_schema: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Content {
    #[serde(rename = "text")]
    Text(TextContent),
    #[serde(rename = "image")]
    ImageContent(ImageContent),
    #[serde(rename = "audio")]
    AudioContent(AudioContent),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextContent {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageContent {
    pub data: String,
    #[serde(rename = "mimeType")]
    pub mime_type: String,
}

impl ImageContent {
    pub fn new(data: String, mime_type: String, _annotations: Option<serde_json::Value>, _metadata: Option<serde_json::Value>) -> Self {
        Self { data, mime_type }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioContent {
    pub data: String,
    #[serde(rename = "mimeType")]
    pub mime_type: String,
}

impl AudioContent {
    pub fn new(data: String, mime_type: String, _annotations: Option<serde_json::Value>, _metadata: Option<serde_json::Value>) -> Self {
        Self { data, mime_type }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CallToolResult {
    pub content: Vec<Content>,
    #[serde(rename = "isError", skip_serializing_if = "Option::is_none")]
    pub is_error: Option<bool>,
}

impl CallToolResult {
    pub fn image_content(content: Vec<ImageContent>) -> Self {
        Self {
            content: content.into_iter().map(|c| Content::ImageContent(c)).collect(),
            is_error: Some(false),
        }
    }

    pub fn audio_content(content: Vec<AudioContent>) -> Self {
        Self {
            content: content.into_iter().map(|c| Content::AudioContent(c)).collect(),
            is_error: Some(false),
        }
    }

    
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CallToolRequest {
    pub params: CallToolParams,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CallToolParams {
    pub name: String,
    #[serde(default)]
    pub arguments: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListToolsRequest {
    pub params: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ListToolsResult {
    pub tools: Vec<Tool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<serde_json::Value>,
    #[serde(rename = "nextCursor", skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InitializeRequest {
    pub params: InitializeParams,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InitializeParams {
    #[serde(rename = "protocolVersion")]
    pub protocol_version: String,
    pub capabilities: HashMap<String, serde_json::Value>,
    #[serde(rename = "clientInfo")]
    pub client_info: ClientInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientInfo {
    pub name: String,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InitializeResult {
    #[serde(rename = "protocolVersion")]
    pub protocol_version: String,
    pub capabilities: HashMap<String, serde_json::Value>,
    #[serde(rename = "serverInfo")]
    pub server_info: ServerInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerInfo {
    pub name: String,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RpcError {
    pub code: i32,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
}

impl RpcError {
    
}

#[derive(Debug, Clone)]
pub struct CallToolError {
    pub message: String,
}

impl CallToolError {
    pub fn new<E: std::fmt::Display>(error: E) -> Self {
        Self {
            message: error.to_string(),
        }
    }
}

impl std::fmt::Display for CallToolError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for CallToolError {}