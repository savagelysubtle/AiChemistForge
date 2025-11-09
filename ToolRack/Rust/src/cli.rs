use clap::{arg, command, Parser};

#[derive(Parser, Debug)]
#[command(name =  env!("CARGO_PKG_NAME"))]
#[command(version = env!("CARGO_PKG_VERSION"))]
#[command(about = "A lightning-fast, asynchronous, and lightweight MCP server designed for efficient handling of various filesystem operations",
long_about = None)]
pub struct CommandArguments {
    #[arg(
        long,
        num_args = 0..,
        value_delimiter = ',',
        help = "Comma-separated list of directories blocked from access.",
        long_help = "Provide comma-separated directories blocked from operation. Example: --blocked-directories 'C:\\Windows,C:\\Program Files,C:\\CustomBlocked'"
    )]
    pub blocked_directories: Vec<String>,

    #[arg(
        help = "List of directories that are permitted for the operation. Leave empty for unrestricted access (except blocked directories)."
    )]
    pub allowed_directories: Vec<String>,
}

impl CommandArguments {
    pub fn parse_from_env() -> anyhow::Result<Self> {
        let args = Self::parse();
        Ok(args)
    }
}