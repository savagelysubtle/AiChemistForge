use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, AudioContent, ImageContent, CallToolError};
use crate::error::ServiceError;
use crate::fs_service::FileSystemService;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadMediaFile {
    pub path: String,
    pub max_bytes: Option<u64>,
}

impl ReadMediaFile {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let (kind, content) = fs_service
            .read_media_file(
                Path::new(&self.path),
                self.max_bytes.map(|v| v as usize),
            )
            .await
            .map_err(CallToolError::new)?;

        let mime_type = kind.mime_type().to_string();
        let call_result = match kind.matcher_type() {
            infer::MatcherType::Image => {
                let image_content = ImageContent::new(content, mime_type, None, None);
                CallToolResult::image_content(vec![image_content])
            }
            infer::MatcherType::Audio => {
                let audio_content = AudioContent::new(content, mime_type, None, None);
                CallToolResult::audio_content(vec![audio_content])
            }
            _ => {
                return Err(CallToolError::new(
                    ServiceError::InvalidMediaFile(mime_type)
                ));
            }
        };
        Ok(call_result)
    }
}
