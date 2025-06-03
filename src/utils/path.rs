use std::path::Path;

/// Encode a filesystem path to Claude Code's project directory naming convention
/// 
/// Examples:
/// - `/Users/darin/Projects/apply-model` → `-Users-darin-Projects-apply-model`
/// - `/Users/darin/.claude` → `-Users-darin--claude`
pub fn encode_project_path(path: &Path) -> String {
    let path_str = path.to_string_lossy();
    let chars: Vec<char> = path_str.chars().collect();
    let mut encoded = String::new();
    
    let mut i = 0;
    while i < chars.len() {
        if chars[i] == '/' {
            // Check if next char is a dot (hidden directory)
            if i + 1 < chars.len() && chars[i + 1] == '.' {
                encoded.push('-');
                encoded.push('-');
                i += 2; // Skip the slash and dot
            } else {
                encoded.push('-');
                i += 1;
            }
        } else {
            encoded.push(chars[i]);
            i += 1;
        }
    }
    
    encoded
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
    fn test_encode_project_path() {
        let path = Path::new("/Users/darin/Projects/apply-model");
        assert_eq!(encode_project_path(path), "-Users-darin-Projects-apply-model");
        
        let hidden_path = Path::new("/Users/darin/.claude");
        assert_eq!(encode_project_path(hidden_path), "-Users-darin--claude");
    }

    #[test]
    fn test_extract_project_name() {
        let path = Path::new("/Users/darin/Projects/apply-model");
        assert_eq!(extract_project_name(path), "apply-model");
        
        let hidden_path = Path::new("/Users/darin/.claude");
        assert_eq!(extract_project_name(hidden_path), ".claude");
    }
}