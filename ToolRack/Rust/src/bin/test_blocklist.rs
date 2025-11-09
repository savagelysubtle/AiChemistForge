use aichemistforge_mcp_server::fs_service::FileSystemService;
use std::path::Path;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Testing blocklist functionality...");

    // Test 1: Unrestricted mode with blocklist
    println!("\nTest 1: Unrestricted mode with blocklist");
    let allowed_dirs = vec![];
    let blocked_dirs = vec!["C:\\Windows".to_string(), "C:\\Program Files".to_string()];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Should be allowed (not in blocklist and in unrestricted mode)
    let allowed_path = Path::new("C:\\Temp\\test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    println!("Path {:?} validation result: {:?}", allowed_path, result.is_ok());

    // Should be blocked (in blocklist)
    let blocked_path = Path::new("C:\\Windows\\system32\\config\\sam");
    let result = fs_service.validate_path(blocked_path).await;
    println!("Path {:?} validation result: {:?}", blocked_path, result.is_ok());

    // Test 2: Restricted mode with allowed directories
    println!("\nTest 2: Restricted mode with allowed directories");
    let allowed_dirs = vec!["C:\\Users".to_string(), "C:\\Temp".to_string()];
    let blocked_dirs = vec![];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Should be allowed (in allowed directories)
    let allowed_path = Path::new("C:\\Users\\test\\Documents\\test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    println!("Path {:?} validation result: {:?}", allowed_path, result.is_ok());

    // Should be blocked (not in allowed directories)
    let disallowed_path = Path::new("C:\\Windows\\system32\\drivers\\etc\\hosts");
    let result = fs_service.validate_path(disallowed_path).await;
    println!("Path {:?} validation result: {:?}", disallowed_path, result.is_ok());

    // Test 3: Combined mode with both allowed and blocked directories
    println!("\nTest 3: Combined mode with both allowed and blocked directories");
    let allowed_dirs = vec!["C:\\Users".to_string(), "C:\\Temp".to_string()];
    let blocked_dirs = vec!["C:\\Users\\Public".to_string()];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Should be allowed (in allowed directories and not in blocked directories)
    let allowed_path = Path::new("C:\\Users\\test\\Documents\\test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    println!("Path {:?} validation result: {:?}", allowed_path, result.is_ok());

    // Should be blocked (in blocked directories even though it's in allowed directories)
    let blocked_path = Path::new("C:\\Users\\Public\\test.txt");
    let result = fs_service.validate_path(blocked_path).await;
    println!("Path {:?} validation result: {:?}", blocked_path, result.is_ok());

    // Should be blocked (not in allowed directories)
    let disallowed_path = Path::new("C:\\Windows\\system32\\drivers\\etc\\hosts");
    let result = fs_service.validate_path(disallowed_path).await;
    println!("Path {:?} validation result: {:?}", disallowed_path, result.is_ok());

    println!("\nAll tests completed!");
    Ok(())
}