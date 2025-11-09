use aichemistforge_mcp_server::cli::CommandArguments;
use aichemistforge_mcp_server::handler::MyServerHandler;

/// This example demonstrates how to use the new blocklist functionality
/// Note: The server is now always in read-write mode with no readonly option
fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("AiChemistForge Rust MCP Server - Blocklist Example");
    println!("==================================================");
    println!("Note: The server is always in read-write mode with no readonly option");

    // Example 1: Unrestricted read-write mode with blocklist
    println!("\nExample 1: Unrestricted read-write mode with blocklist");
    println!("This mode allows access to all directories except those explicitly blocked.");
    println!("Note: In production, use comma-separated values via CLI arguments");

    let args = CommandArguments {
        // In real usage: --blocked-directories "C:\\Windows,C:\\Program Files"
        blocked_directories: vec!["C:\\Windows".to_string(), "C:\\Program Files".to_string()],
        allowed_directories: vec![], // Empty means unrestricted
    };

    let handler = MyServerHandler::new(&args)?;
    println!("{}", handler.startup_message());

    // Example 2: Restricted read-write mode
    println!("\n\nExample 2: Restricted read-write mode");
    println!("This mode only allows access to specified directories.");

    let args = CommandArguments {
        blocked_directories: vec![], // No blocked directories
        allowed_directories: vec!["C:\\Users\\MyProject".to_string(), "C:\\Temp".to_string()],
    };

    let handler = MyServerHandler::new(&args)?;
    println!("{}", handler.startup_message());

    // Example 3: Read-write mode with both allowed and blocked directories
    println!("\n\nExample 3: Read-write mode with both allowed and blocked directories");
    println!("This mode allows access to specified directories, except those explicitly blocked.");

    let args = CommandArguments {
        blocked_directories: vec!["C:\\Users\\Public".to_string()],
        allowed_directories: vec!["C:\\Users".to_string(), "C:\\Temp".to_string()],
    };

    let handler = MyServerHandler::new(&args)?;
    println!("{}", handler.startup_message());

    // Example 4: Command-line usage examples
    println!("\n\nExample 4: Command-line Usage");
    println!("=================================");
    println!("Default blocklist only:");
    println!("  cargo run --release -- ");
    println!();
    println!("Default + custom blocklist:");
    println!("  cargo run --release -- --blocked-directories 'D:\\Sensitive,C:\\Private'");
    println!();
    println!("Via MCP JSON config (.gemini/settings.json):");
    println!(r#"  "Rust": {{"#);
    println!(r#"    "command": "path\\to\\start_mcp_server.bat","#);
    println!(r#"    "args": ["--blocked-directories", "D:\\Sensitive,C:\\Private"],"#);
    println!(r#"    "type": "stdio""#);
    println!(r#"  }}"#);

    Ok(())
}