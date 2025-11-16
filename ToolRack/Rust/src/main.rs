mod handler;
mod tools;
mod fs_service;
mod cli;
mod error;
mod mcp_types;
mod server;
mod task_state;
mod retry;

use handler::MyServerHandler;
use cli::CommandArguments;
use server::McpServer;
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    eprintln!("Starting AiChemistForge Rust MCP Server with stdio transport...");
    eprintln!("Logs will appear on stderr, JSON-RPC communication on stdout");

    // Parse command line arguments
    let args = CommandArguments::parse_from_env()?;

    // Create the server handler
    let handler = MyServerHandler::new(&args)?;

    // Create and run the MCP server
    let server = McpServer::new(handler);
    server.run().await?;

    Ok(())
}
