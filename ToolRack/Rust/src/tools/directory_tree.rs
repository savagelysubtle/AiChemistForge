use serde::{Deserialize, Serialize};
use crate::mcp_types::{CallToolResult, CallToolError};
use crate::fs_service::FileSystemService;
use crate::retry::retry_3x;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DirectoryTreeTool {
    /// The **absolute path** of the directory to generate a tree view for
    pub path: String,
    /// Include hidden files and directories in the tree
    #[serde(default)]
    pub include_hidden: bool,
    /// Maximum depth to traverse (0 means unlimited)
    #[serde(default)]
    pub max_depth: u32,
}

impl DirectoryTreeTool {


    pub async fn run_tool(self, fs_service: &FileSystemService) -> Result<CallToolResult, CallToolError> {
        // Retry up to 3 times on transient I/O errors
        let path = self.path.clone();
        let include_hidden = self.include_hidden;
        let max_depth = self.max_depth;
        match retry_3x("directory_tree", || {
            let p = path.clone();
            async move {
                fs_service.generate_directory_tree(std::path::Path::new(&p), include_hidden, max_depth).await
            }
        }).await {
            Ok(tree) => Ok(CallToolResult {
                content: vec![crate::mcp_types::Content::Text(crate::mcp_types::TextContent {
                    text: tree,
                })],
                is_error: Some(false),
            }),
            Err(e) => Err(CallToolError::new(e)),
        }
    }
}
