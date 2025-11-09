use aichemistforge_mcp_server::fs_service::FileSystemService;
use aichemistforge_mcp_server::error::ServiceResult;
use std::path::Path;

#[tokio::test]
async fn test_blocklist_functionality() -> ServiceResult<()> {
    // Test with empty allowed directories (unrestricted mode) and some blocked directories
    let allowed_dirs = vec![];
    let blocked_dirs = vec!["/etc".to_string(), "/var".to_string()];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Verify that allowed directories is empty (unrestricted mode)
    assert!(fs_service.allowed_directories().is_empty());

    // Verify that blocked directories is properly set
    assert_eq!(fs_service.blocked_directories().len(), 2);

    // Test validation with a blocked path (should fail)
    let blocked_path = Path::new("/etc/passwd");
    let result = fs_service.validate_path(blocked_path).await;
    assert!(result.is_err());

    // Test validation with a non-blocked path (should succeed in unrestricted mode)
    let allowed_path = Path::new("/tmp/test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    assert!(result.is_ok());

    Ok(())
}

#[tokio::test]
async fn test_allowed_directories_functionality() -> ServiceResult<()> {
    // Test with specific allowed directories and no blocked directories
    let allowed_dirs = vec!["/home".to_string(), "/tmp".to_string()];
    let blocked_dirs = vec![];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Verify that allowed directories is properly set
    assert_eq!(fs_service.allowed_directories().len(), 2);

    // Verify that blocked directories is empty
    assert!(fs_service.blocked_directories().is_empty());

    // Test validation with an allowed path (should succeed)
    let allowed_path = Path::new("/home/user/test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    assert!(result.is_ok());

    // Test validation with a non-allowed path (should fail)
    let disallowed_path = Path::new("/etc/passwd");
    let result = fs_service.validate_path(disallowed_path).await;
    assert!(result.is_err());

    Ok(())
}

#[tokio::test]
async fn test_combined_allowed_and_blocked() -> ServiceResult<()> {
    // Test with both allowed and blocked directories
    let allowed_dirs = vec!["/home".to_string(), "/tmp".to_string()];
    let blocked_dirs = vec!["/home/user/secret".to_string()];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Verify that both allowed and blocked directories are properly set
    assert_eq!(fs_service.allowed_directories().len(), 2);
    assert_eq!(fs_service.blocked_directories().len(), 1);

    // Test validation with an allowed but not blocked path (should succeed)
    let allowed_path = Path::new("/home/user/documents/test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    assert!(result.is_ok());

    // Test validation with a blocked path within allowed directories (should fail)
    let blocked_path = Path::new("/home/user/secret/passwords.txt");
    let result = fs_service.validate_path(blocked_path).await;
    assert!(result.is_err());

    // Test validation with a path outside allowed directories (should fail)
    let disallowed_path = Path::new("/etc/passwd");
    let result = fs_service.validate_path(disallowed_path).await;
    assert!(result.is_err());

    Ok(())
}

#[tokio::test]
async fn test_windows_paths_with_comma_separation() -> ServiceResult<()> {
    // Test Windows-style paths that would come from comma-separated CLI args
    let allowed_dirs = vec![];
    let blocked_dirs = vec![
        "C:\\Windows".to_string(),
        "C:\\Program Files".to_string(),
        "C:\\Program Files (x86)".to_string(),
    ];

    let fs_service = FileSystemService::try_new(&allowed_dirs, &blocked_dirs)?;

    // Verify that allowed directories is empty (unrestricted mode)
    assert!(fs_service.allowed_directories().is_empty());

    // Verify that blocked directories is properly set
    assert_eq!(fs_service.blocked_directories().len(), 3);

    // Test that non-blocked paths work in unrestricted mode
    let allowed_path = Path::new("D:\\Projects\\test.txt");
    let result = fs_service.validate_path(allowed_path).await;
    assert!(result.is_ok());

    Ok(())
}