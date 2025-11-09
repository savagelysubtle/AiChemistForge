use serde::{Deserialize, Serialize};
use crate::fs_service::{FileSearchResult, FileSystemService};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use std::fmt::Write;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchFilesContent {
    pub path: String,
    pub pattern: String,
    pub query: String,
    pub is_regex: Option<bool>,
    #[serde(rename = "excludePatterns")]
    pub exclude_patterns: Option<Vec<String>>,
    pub min_bytes: Option<u64>,
    pub max_bytes: Option<u64>,
}

impl SearchFilesContent {
    

    fn format_result(&self, results: Vec<FileSearchResult>) -> String {
        // TODO: improve capacity estimation
        let estimated_capacity = 2048;
        let mut output = String::with_capacity(estimated_capacity);
        for file_result in results {
            // Push file path
            let _ = writeln!(output, "{}", file_result.file_path.display());
            // Push each match line
            for m in &file_result.matches {
                // Format: "  line:col: text snippet"
                let _ = writeln!(
                    output,
                    "  {}:{}: {}",
                    m.line_number, m.start_pos, m.line_text
                );
            }
            // double spacing
            output.push('\n');
        }
        output
    }

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let is_regex = self.is_regex.unwrap_or_default();
        match fs_service
            .search_files_content(
                &self.path,
                &self.pattern,
                &self.query,
                is_regex,
                self.exclude_patterns.to_owned(),
                self.min_bytes,
                self.max_bytes,
            )
            .await
        {
            Ok(results) => {
                if results.is_empty() {
                    return Ok(CallToolResult {
                        content: vec![],
                        is_error: Some(true),
                    });
                }
                Ok(CallToolResult {
                    content: vec![Content::Text(TextContent {
                        text: self.format_result(results),
                    })],
                    is_error: Some(false),
                })
            }
            Err(_err) => Ok(CallToolResult {
                content: vec![],
                is_error: Some(true),
            }),
        }
    }
}
