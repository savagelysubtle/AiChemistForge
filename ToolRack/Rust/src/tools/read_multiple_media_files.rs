use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, AudioContent, ImageContent, CallToolError};
use crate::fs_service::FileSystemService;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadMultipleMediaFiles {
    pub paths: Vec<String>,
    pub max_bytes: Option<u64>,
}

impl ReadMultipleMediaFiles {
    

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let result = fs_service
            .read_media_files(self.paths, self.max_bytes.map(|v| v as usize))
            .await
            .map_err(CallToolError::new)?;

        let content: Vec<_> = result
            .into_iter()
            .filter_map(|(kind, content)| {
                let mime_type = kind.mime_type().to_string();
                match kind.matcher_type() {
                    infer::MatcherType::Image => Some(Content::ImageContent(
                        ImageContent::new(content, mime_type, None, None),
                    )),
                    infer::MatcherType::Audio => Some(Content::AudioContent(
                        AudioContent::new(content, mime_type, None, None),
                    )),
                    _ => None,
                }
            })
            .collect();

        Ok(CallToolResult {
            content,
            is_error: Some(false),
        })
    }
}
