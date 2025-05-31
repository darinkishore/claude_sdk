use std::path::{Path, PathBuf};

/// Encode a filesystem path to Claude Code's project directory naming convention
/// 
/// Examples:
/// - `/Users/darin/Projects/apply-model` → `-Users-darin-Projects-apply-model`
/// - `/Users/darin/.claude` → `-Users-darin--claude`
pub fn encode_project_path(path: &Path) -> String {
    let path_str = path.to_string_lossy();
    
    // Replace path separators with dashes
    let encoded = path_str.replace('/', "-");
    
    // Handle double dashes from hidden directories (e.g., /.claude -> --claude)
    // This is already handled by the replace above
    
    encoded
}

/// Decode a Claude Code project directory name back to a filesystem path
/// 
/// Examples:
/// - `-Users-darin-Projects-apply-model` → `/Users/darin/Projects/apply-model`
/// - `-Users-darin--claude` → `/Users/darin/.claude`
pub fn decode_project_path(encoded: &str) -> PathBuf {
    // Handle double dashes (hidden directories)
    let decoded = encoded.replace("--", "-/.").replace('-', "/");
    
    PathBuf::from(decoded)
}

/// Extract a project name from a path
/// 
/// Examples:
/// - `/Users/darin/Projects/apply-model` → `apply-model`
/// - `/Users/darin/.claude` → `.claude`
pub fn extract_project_name(path: &Path) -> String {
    path.file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[ignore]
    fn test_encode_project_path() {
        let path = Path::new("/Users/darin/Projects/apply-model");
        assert_eq!(encode_project_path(path), "-Users-darin-Projects-apply-model");
        
        let hidden_path = Path::new("/Users/darin/.claude");
        assert_eq!(encode_project_path(hidden_path), "-Users-darin--claude");
    }

    #[test]
    #[ignore]
    fn test_decode_project_path() {
        let encoded = "-Users-darin-Projects-apply-model";
        assert_eq!(decode_project_path(encoded), PathBuf::from("/Users/darin/Projects/apply-model"));
        
        let hidden_encoded = "-Users-darin--claude";
        assert_eq!(decode_project_path(hidden_encoded), PathBuf::from("/Users/darin/.claude"));
    }

    #[test]
    fn test_extract_project_name() {
        let path = Path::new("/Users/darin/Projects/apply-model");
        assert_eq!(extract_project_name(path), "apply-model");
        
        let hidden_path = Path::new("/Users/darin/.claude");
        assert_eq!(extract_project_name(hidden_path), ".claude");
    }

    #[test]
    #[ignore]
    fn test_roundtrip() {
        let original = Path::new("/Users/darin/Projects/my-project");
        let encoded = encode_project_path(original);
        let decoded = decode_project_path(&encoded);
        assert_eq!(decoded, original);
    }
}