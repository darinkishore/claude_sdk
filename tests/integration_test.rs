use claude_sdk::SessionParser;
use std::path::PathBuf;
use std::env;

/// Get the Claude projects directory, checking environment variables
fn get_claude_projects_dir() -> Option<PathBuf> {
    // First check if we're on darin's machine
    if env::var("USER").ok()? == "darin" {
        let path = PathBuf::from("/Users/darin/.claude/projects");
        if path.exists() {
            return Some(path);
        }
    }
    
    // Otherwise check XDG_CONFIG_HOME
    if let Ok(xdg_config) = env::var("XDG_CONFIG_HOME") {
        let path = PathBuf::from(xdg_config).join("claude/projects");
        if path.exists() {
            return Some(path);
        }
    }
    
    // Default to ~/.config/claude/projects
    if let Some(home) = env::var("HOME").ok() {
        let path = PathBuf::from(home).join(".config/claude/projects");
        if path.exists() {
            return Some(path);
        }
    }
    
    None
}

#[test]
#[ignore] // Use `cargo test -- --ignored` to run integration tests
fn test_parse_real_sessions() {
    // Run with larger stack size to handle deeply nested conversations
    std::thread::Builder::new()
        .stack_size(8 * 1024 * 1024) // 8MB stack
        .spawn(|| {
            test_parse_real_sessions_impl();
        })
        .unwrap()
        .join()
        .unwrap();
}

fn test_parse_real_sessions_impl() {
    let projects_dir = match get_claude_projects_dir() {
        Some(dir) => dir,
        None => {
            tracing::warn!("Claude projects directory not found, skipping integration tests");
            return;
        }
    };
    
    // Find all JSONL files
    let session_files = SessionParser::discover_sessions(&projects_dir).unwrap();
    
    assert!(!session_files.is_empty(), "No session files found in {:?}", projects_dir);
    
    println!("Found {} session files", session_files.len());
    
    let mut total_parsed = 0;
    let mut total_errors = 0;
    let mut sessions_with_tools = 0;
    let mut sessions_with_branches = 0;
    let mut empty_file_errors = 0;
    let mut other_errors = Vec::new();
    
    // Parse ALL files to find the problematic one
    let total_files = session_files.len();
    for (i, file_path) in session_files.iter().enumerate() {
        if i % 50 == 0 || i == total_files - 1 {
            print!("\rProgress: {}/{} files...", i + 1, total_files);
            use std::io::{self, Write};
            io::stdout().flush().unwrap();
        }
        
        let parser = SessionParser::new(file_path);
        
        match parser.parse() {
            Ok(session) => {
                total_parsed += 1;
                
                if !session.metadata.unique_tools_used.is_empty() {
                    sessions_with_tools += 1;
                }
                
                let stats = session.conversation_tree.stats();
                if stats.num_branches > 0 {
                    sessions_with_branches += 1;
                }
                
                // Verify tree consistency
                assert_eq!(
                    session.messages.len(), 
                    stats.total_messages,
                    "Message count mismatch in tree"
                );
            }
            Err(e) => {
                total_errors += 1;
                
                match e {
                    claude_sdk::ClaudeError::ParseError(claude_sdk::ParseError::EmptyFile) => {
                        empty_file_errors += 1;
                    }
                    _ => {
                        other_errors.push((file_path.clone(), e.to_string()));
                    }
                }
            }
        }
    }
    
    println!("\n=== Summary ===");
    println!("Total tested: {}", total_parsed + total_errors);
    println!("Successfully parsed: {}", total_parsed);
    println!("Errors: {}", total_errors);
    println!("  - Empty files: {}", empty_file_errors);
    println!("  - Other errors: {}", other_errors.len());
    println!("Sessions with tools: {}", sessions_with_tools);
    println!("Sessions with branches: {}", sessions_with_branches);
    
    if !other_errors.is_empty() {
        println!("\n=== Non-empty file errors ===");
        for (path, error) in other_errors.iter().take(10) {
            println!("File: {}", path.file_name().unwrap().to_string_lossy());
            println!("Error: {}\n", error);
        }
        if other_errors.len() > 10 {
            println!("... and {} more errors", other_errors.len() - 10);
        }
    }
    
    // At least 50% should parse successfully (some files may be empty or corrupted)
    assert!(
        total_parsed as f64 / (total_parsed + total_errors) as f64 >= 0.5,
        "Too many parsing errors"
    );
}

#[test]
#[ignore]
fn test_large_session_performance() {
    let projects_dir = match get_claude_projects_dir() {
        Some(dir) => dir,
        None => {
            tracing::warn!("Claude projects directory not found, skipping test");
            return;
        }
    };
    
    // Find large files (> 1MB)
    let session_files = SessionParser::discover_sessions(&projects_dir).unwrap();
    let large_files: Vec<_> = session_files
        .into_iter()
        .filter(|path| {
            path.metadata()
                .map(|m| m.len() > 1_000_000)
                .unwrap_or(false)
        })
        .collect();
    
    if large_files.is_empty() {
        println!("No large session files found, skipping performance test");
        return;
    }
    
    println!("Testing {} large session files", large_files.len());
    
    for file_path in large_files.iter().take(3) {
        let file_size = file_path.metadata().unwrap().len();
        println!("\nTesting file: {:?} ({:.2} MB)", 
            file_path.file_name().unwrap(),
            file_size as f64 / 1_000_000.0
        );
        
        let start = std::time::Instant::now();
        let parser = SessionParser::new(file_path);
        let result = parser.parse();
        let elapsed = start.elapsed();
        
        match result {
            Ok(session) => {
                println!("  ✓ Parsed in {:.2}s", elapsed.as_secs_f64());
                println!("    Messages: {}", session.metadata.total_messages);
                println!("    Messages/sec: {:.0}", 
                    session.metadata.total_messages as f64 / elapsed.as_secs_f64()
                );
                
                // Performance assertion: should parse at least 1000 messages/sec
                assert!(
                    session.metadata.total_messages as f64 / elapsed.as_secs_f64() > 1000.0,
                    "Parsing too slow"
                );
            }
            Err(e) => {
                println!("  ✗ Error: {}", e);
            }
        }
    }
}

#[test]
#[ignore]
fn test_tool_extraction_real_data() {
    let projects_dir = match get_claude_projects_dir() {
        Some(dir) => dir,
        None => {
            tracing::warn!("Claude projects directory not found, skipping test");
            return;
        }
    };
    
    let session_files = SessionParser::discover_sessions(&projects_dir).unwrap();
    let mut found_tools = false;
    
    // Find a session with tool usage
    for file_path in session_files.iter().take(20) {
        let parser = SessionParser::new(file_path);
        
        if let Ok(tools) = parser.extract_tool_usage() {
            if !tools.is_empty() {
                found_tools = true;
                println!("\nFound session with tools: {:?}", file_path.file_name().unwrap());
                println!("Tool executions: {}", tools.len());
                
                for (i, exec) in tools.iter().take(5).enumerate() {
                    println!("\n  Tool {}: {}", i + 1, exec.tool_name);
                    println!("    Success: {}", exec.is_success());
                    println!("    Duration: {}ms", exec.duration_ms());
                    
                    // Basic validation
                    assert!(!exec.tool_name.is_empty());
                }
                
                // Analyze patterns
                let patterns = claude_sdk::utils::analyze_tool_patterns(&tools);
                println!("\nTool usage patterns:");
                for pattern in patterns.iter().take(5) {
                    println!("  {}: {} calls, {:.1}% success rate, avg {:.0}ms",
                        pattern.tool_name,
                        pattern.frequency,
                        pattern.success_rate * 100.0,
                        pattern.avg_duration_ms
                    );
                }
                
                break;
            }
        }
    }
    
    assert!(found_tools, "No sessions with tool usage found in sample");
}

#[test]
#[ignore]
fn test_session_info_quick_scan() {
    let projects_dir = match get_claude_projects_dir() {
        Some(dir) => dir,
        None => {
            tracing::warn!("Claude projects directory not found, skipping test");
            return;
        }
    };
    
    let session_files = SessionParser::discover_sessions(&projects_dir).unwrap();
    
    println!("Quick scanning {} session files", session_files.len());
    
    let start = std::time::Instant::now();
    let mut total_messages = 0;
    let mut oldest_timestamp = None;
    let mut newest_timestamp = None;
    
    for file_path in &session_files {
        let parser = SessionParser::new(file_path);
        
        if let Ok(info) = parser.session_info() {
            total_messages += info.message_count;
            
            if let Some(ts) = info.first_timestamp {
                oldest_timestamp = Some(match oldest_timestamp {
                    None => ts,
                    Some(old) => if ts < old { ts } else { old },
                });
            }
            
            if let Some(ts) = info.last_timestamp {
                newest_timestamp = Some(match newest_timestamp {
                    None => ts,
                    Some(new) => if ts > new { ts } else { new },
                });
            }
        }
    }
    
    let elapsed = start.elapsed();
    
    println!("\nScanned {} files in {:.2}s", session_files.len(), elapsed.as_secs_f64());
    println!("Total messages across all sessions: {}", total_messages);
    
    if let (Some(oldest), Some(newest)) = (oldest_timestamp, newest_timestamp) {
        println!("Date range: {} to {}", oldest.format("%Y-%m-%d"), newest.format("%Y-%m-%d"));
    }
    
    // Should be able to scan at least 100 files/sec
    assert!(
        session_files.len() as f64 / elapsed.as_secs_f64() > 100.0,
        "Session info scanning too slow"
    );
}