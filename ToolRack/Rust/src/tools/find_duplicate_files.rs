use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, Content, TextContent, CallToolError};
use crate::fs_service::FileSystemService;
use std::{collections::BTreeMap, fmt::Write};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FindDuplicateFiles {
    pub root_path: String,
    pub pattern: Option<String>,
    pub exclude_patterns: Option<Vec<String>>,
    pub min_bytes: Option<u64>,
    pub max_bytes: Option<u64>,
    pub output_format: Option<String>,
}

impl FindDuplicateFiles {
    

    fn format_output(
        duplicate_files: Vec<Vec<String>>,
        output_format: &str,
    ) -> Result<String, String> {
        match output_format {
            "json" => {
                // Use a map to hold string keys and array values
                let mut map = BTreeMap::new();
                for (i, group) in duplicate_files.into_iter().enumerate() {
                    map.insert(i.to_string(), group);
                }
                // Serialize the map to a pretty JSON string
                Ok(serde_json::to_string_pretty(&map).map_err(|e| e.to_string())?)
            }
            _ => {
                let mut output = String::new();
                let header = if duplicate_files.is_empty() {
                    "No duplicate files were found.".to_string()
                } else {
                    format!("Found {} sets of duplicate files:\n", duplicate_files.len(),)
                };
                output.push_str(&header);
                for (i, group) in duplicate_files.iter().enumerate() {
                    writeln!(output, "\nDuplicated Group {}:", i + 1)
                        .map_err(|e| e.to_string())?;
                    for file in group {
                        writeln!(output, "  {file}").map_err(|e| e.to_string())?;
                    }
                }
                Ok(output)
            }
        }
    }

    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        let duplicate_files = fs_service
            .find_duplicate_files(
                std::path::Path::new(&self.root_path),
                self.pattern.clone(),
                self.exclude_patterns.clone(),
                self.min_bytes.or(Some(1)),
                self.max_bytes,
            )
            .await
            .map_err(CallToolError::new)?;

        let output_format = self.output_format.as_deref().unwrap_or("text");
        let result_content = Self::format_output(duplicate_files, output_format)
            .map_err(CallToolError::new)?;

        Ok(CallToolResult {
            content: vec![Content::Text(TextContent {
                text: result_content,
            })],
            is_error: Some(false),
        })
    }
}
