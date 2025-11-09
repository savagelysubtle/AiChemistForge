// Individual tool modules (kept for implementation but not exposed)
pub mod edit_operation;
pub mod directory_tree;
pub mod list_allowed_directories;
pub mod read_file;
pub mod read_multiple_files;
pub mod write_file;
pub mod edit_file;
pub mod create_directory;
pub mod list_directory;
pub mod move_file;
pub mod search_files;
pub mod get_file_info;
pub mod zip_files;
pub mod unzip_file;
pub mod zip_directory;
pub mod copy_file;
pub mod delete_file;
// New tool modules
pub mod calculate_directory_size;
pub mod find_duplicate_files;
pub mod find_empty_directories;
pub mod head_file;
pub mod list_directory_with_sizes;
pub mod read_file_lines;
pub mod read_media_file;
pub mod read_multiple_media_files;
pub mod search_files_content;
pub mod tail_file;

// Dynamic operation mode tools
pub mod single_file_operations;
pub mod multiple_file_operations;
pub mod directory_operations;
pub mod search_and_analysis;
pub mod file_management;
pub mod operation_mode_management;

// Note: task_state is accessed directly from crate root

// Individual tool structs (kept for implementation but not exposed)
pub use edit_operation::EditOperation;
pub use directory_tree::DirectoryTreeTool;
pub use list_allowed_directories::ListAllowedDirectoriesTool;
pub use read_file::ReadFileTool;
pub use read_multiple_files::ReadMultipleFilesTool;
pub use write_file::WriteFileTool;
pub use edit_file::EditFileTool;
pub use create_directory::CreateDirectoryTool;
pub use list_directory::ListDirectoryTool;
pub use move_file::MoveFileTool;
pub use search_files::SearchFilesTool;
pub use get_file_info::GetFileInfoTool;
pub use zip_files::ZipFilesTool;
pub use unzip_file::UnzipFileTool;
pub use zip_directory::ZipDirectoryTool;
pub use copy_file::CopyFileTool;
pub use delete_file::DeleteFileTool;
// New tool structs
pub use calculate_directory_size::CalculateDirectorySize;
pub use find_duplicate_files::FindDuplicateFiles;
pub use find_empty_directories::FindEmptyDirectories;
pub use head_file::HeadFile;
pub use list_directory_with_sizes::ListDirectoryWithSizes;
pub use read_file_lines::ReadFileLines;
pub use read_media_file::ReadMediaFile;
pub use read_multiple_media_files::ReadMultipleMediaFiles;
pub use search_files_content::SearchFilesContent;
pub use tail_file::TailFile;

// Dynamic operation mode tools
pub use single_file_operations::SingleFileOperationsTool;
pub use multiple_file_operations::MultipleFileOperationsTool;
pub use directory_operations::DirectoryOperationsTool;
pub use search_and_analysis::SearchAndAnalysisTool;
pub use file_management::FileManagementTool;

// Operation mode management tools
pub use operation_mode_management::{StartOperationModeTool, CompleteCurrentModeTool, ListAvailableModesTool, GetCurrentModeStatusTool};

use crate::mcp_types::*;

// Enum for dynamic operation mode tools (only these are exposed to clients)
#[derive(Debug, Clone)]
pub enum FileSystemTools {
    SingleFileOperationsTool(SingleFileOperationsTool),
    MultipleFileOperationsTool(MultipleFileOperationsTool),
    DirectoryOperationsTool(DirectoryOperationsTool),
    SearchAndAnalysisTool(SearchAndAnalysisTool),
    FileManagementTool(FileManagementTool),
    // Operation mode management tools
    StartOperationMode(StartOperationModeTool),
    CompleteCurrentMode(CompleteCurrentModeTool),
    ListAvailableModes(ListAvailableModesTool),
    GetCurrentModeStatus(GetCurrentModeStatusTool),
}

impl FileSystemTools {
    pub fn tools() -> Vec<Tool> {
        vec![
            SingleFileOperationsTool::tool_definition(),
            MultipleFileOperationsTool::tool_definition(),
            DirectoryOperationsTool::tool_definition(),
            SearchAndAnalysisTool::tool_definition(),
            FileManagementTool::tool_definition(),
            // Operation mode management tools
            StartOperationModeTool::tool_definition(),
            CompleteCurrentModeTool::tool_definition(),
            ListAvailableModesTool::tool_definition(),
            GetCurrentModeStatusTool::tool_definition(),
        ]
    }

    pub fn require_write_access(&self) -> bool {
        match self {
            Self::SingleFileOperationsTool(_)
            | Self::MultipleFileOperationsTool(_)
            | Self::DirectoryOperationsTool(_)
            | Self::SearchAndAnalysisTool(_)
            | Self::FileManagementTool(_) => true, // These tools can perform write operations
            // Operation mode management tools are read-only
            Self::StartOperationMode(_)
            | Self::CompleteCurrentMode(_)
            | Self::ListAvailableModes(_)
            | Self::GetCurrentModeStatus(_) => false,
        }
    }
}

impl TryFrom<CallToolParams> for FileSystemTools {
    type Error = String;

    fn try_from(params: CallToolParams) -> Result<Self, Self::Error> {
        match params.name.as_str() {
            "single_file_operations" => Ok(Self::SingleFileOperationsTool(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "multiple_file_operations" => Ok(Self::MultipleFileOperationsTool(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "directory_operations" => Ok(Self::DirectoryOperationsTool(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "search_and_analysis" => Ok(Self::SearchAndAnalysisTool(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "file_management" => Ok(Self::FileManagementTool(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            // Operation mode management tools
            "start_operation_mode" => Ok(Self::StartOperationMode(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "complete_current_mode" => Ok(Self::CompleteCurrentMode(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "list_available_modes" => Ok(Self::ListAvailableModes(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            "get_current_mode_status" => Ok(Self::GetCurrentModeStatus(serde_json::from_value(params.arguments.unwrap_or_default()).map_err(|e| e.to_string())?)),
            _ => Err(format!("Unknown tool: {}", params.name)),
        }
    }
}