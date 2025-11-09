use thiserror::Error;
pub type ServiceResult<T> = core::result::Result<T, ServiceError>;

#[derive(Debug, Error)]
pub enum ServiceError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Path is outside allowed directories")]
    PathNotAllowed,
    #[error("Directory already exists")]
    DirectoryAlreadyExists,
    #[error("File not found: {0}")]
    FileNotFound(String),
    #[error("Permission denied")]
    PermissionDenied,

    #[error("{0}")]
    ContentSearchError(#[from] grep::regex::Error),

    #[error("The file is either not an image/audio type or is unsupported (mime:{0}).")]
    InvalidMediaFile(String),
}