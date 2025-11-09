pub mod mcp_types;
pub mod tools;
pub mod handler;
pub mod fs_service;
pub mod cli;
pub mod error;
pub mod task_state;

pub use handler::MyServerHandler;
pub use fs_service::FileSystemService;
pub use cli::CommandArguments;
pub use task_state::*;

// Re-export task state functions for use in tools
pub use task_state::{get_current_mode, add_workflow_step, complete_current_mode, get_available_operation_modes, get_operation_mode_tools, start_operation_mode};
