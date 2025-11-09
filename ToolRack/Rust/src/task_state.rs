use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use std::sync::Mutex;
use once_cell::sync::Lazy;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStep {
    pub step_name: String,
    pub timestamp: DateTime<Utc>,
    pub result_summary: String,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperationMode {
    pub name: String,
    pub start_time: DateTime<Utc>,
    pub context: HashMap<String, serde_json::Value>,
    pub workflow_history: Vec<WorkflowStep>,
    pub available_tools: Vec<String>,
}

impl OperationMode {
    pub fn new(name: String, available_tools: Vec<String>) -> Self {
        Self {
            name,
            start_time: Utc::now(),
            context: HashMap::new(),
            workflow_history: Vec::new(),
            available_tools,
        }
    }

    pub fn add_workflow_step(&mut self, step_name: String, result: serde_json::Value, metadata: Option<HashMap<String, serde_json::Value>>) {
        let step = WorkflowStep {
            step_name,
            timestamp: Utc::now(),
            result_summary: result.to_string().chars().take(200).collect(),
            metadata: metadata.unwrap_or_default(),
        };
        self.workflow_history.push(step);
    }

    pub fn get_workflow_summary(&self) -> HashMap<String, serde_json::Value> {
        let mut summary = HashMap::new();
        summary.insert("mode_name".to_string(), json!(self.name));
        summary.insert("start_time".to_string(), json!(self.start_time.to_rfc3339()));
        summary.insert("duration_seconds".to_string(), json!(Utc::now().timestamp() - self.start_time.timestamp()));
        summary.insert("steps_completed".to_string(), json!(self.workflow_history.len()));
        summary.insert("available_tools".to_string(), json!(self.available_tools));

        let workflow_steps: Vec<HashMap<String, serde_json::Value>> = self.workflow_history
            .iter()
            .map(|step| {
                let mut step_map = HashMap::new();
                step_map.insert("step".to_string(), json!(step.step_name));
                step_map.insert("timestamp".to_string(), json!(step.timestamp.to_rfc3339()));
                step_map.insert("summary".to_string(), json!(step.result_summary));
                step_map
            })
            .collect();

        summary.insert("workflow_steps".to_string(), json!(workflow_steps));
        summary
    }
}

// Global state for current operation mode
static CURRENT_MODE: Lazy<Mutex<Option<OperationMode>>> = Lazy::new(|| Mutex::new(None));

pub fn start_operation_mode(name: String, available_tools: Vec<String>) -> OperationMode {
    let mode = OperationMode::new(name, available_tools);
    *CURRENT_MODE.lock().unwrap() = Some(mode.clone());
    mode
}

pub fn get_current_mode() -> Option<OperationMode> {
    CURRENT_MODE.lock().unwrap().clone()
}

pub fn complete_current_mode() -> Option<OperationMode> {
    CURRENT_MODE.lock().unwrap().take()
}

pub fn add_workflow_step(step_name: String, result: serde_json::Value, metadata: Option<HashMap<String, serde_json::Value>>) {
    if let Some(ref mut mode) = *CURRENT_MODE.lock().unwrap() {
        mode.add_workflow_step(step_name, result, metadata);
    }
}

// Define the operation modes and their available tools
pub fn get_operation_mode_tools(mode_name: &str) -> Vec<String> {
    match mode_name {
        "single_file_operations" => vec![
            "read_file".to_string(),
            "write_file".to_string(),
            "edit_file".to_string(),
            "get_file_info".to_string(),
            "head_file".to_string(),
            "tail_file".to_string(),
            "read_file_lines".to_string(),
            "read_media_file".to_string(),
        ],
        "multiple_file_operations" => vec![
            "read_multiple_files".to_string(),
            "read_multiple_media_files".to_string(),
            "copy_file".to_string(),
            "move_file".to_string(),
            "zip_files".to_string(),
            "unzip_file".to_string(),
            "zip_directory".to_string(),
        ],
        "directory_operations" => vec![
            "create_directory".to_string(),
            "list_directory".to_string(),
            "directory_tree".to_string(),
            "list_directory_with_sizes".to_string(),
            "calculate_directory_size".to_string(),
            "find_empty_directories".to_string(),
            "delete_file".to_string(), // for directories
        ],
        "search_and_analysis" => vec![
            "search_files".to_string(),
            "search_files_content".to_string(),
            "find_duplicate_files".to_string(),
        ],
        "file_management" => vec![
            "list_allowed_directories".to_string(),
            "delete_file".to_string(), // for files
        ],
        _ => vec![],
    }
}

pub fn get_available_operation_modes() -> Vec<String> {
    vec![
        "single_file_operations".to_string(),
        "multiple_file_operations".to_string(),
        "directory_operations".to_string(),
        "search_and_analysis".to_string(),
        "file_management".to_string(),
    ]
}
