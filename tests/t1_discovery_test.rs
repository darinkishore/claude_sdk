// Discovery test to figure out Claude's project directory naming pattern
// Run with: cargo test --test t1_discovery_test -- --ignored --nocapture

mod common;

use claude_sdk::execution::{ClaudeExecutor, ClaudePrompt};
use common::TestEnvironment;

#[test]
#[ignore]
fn discover_claude_project_naming() {
    println!("\n=== Claude Project Directory Discovery Test ===\n");
    
    // Setup test environment
    let mut env = TestEnvironment::setup();
    println!("Test workspace: {:?}", env.workspace);
    
    // Create executor in our test workspace
    let executor = ClaudeExecutor::new(env.workspace.clone())
        .expect("Failed to create ClaudeExecutor");
    
    // Execute a simple prompt
    println!("\nExecuting Claude in test workspace...");
    let prompt = ClaudePrompt {
        text: "Create a file called discovery.txt with the text 'Found me!'".to_string(),
        continue_session: false,
        resume_session_id: None,
    };
    
    let execution = executor.execute(prompt)
        .expect("Failed to execute prompt");
    
    println!("Session ID: {}", execution.session_id);
    println!("Response: {}", execution.response);
    
    // Now discover where Claude created the project
    println!("\nDiscovering Claude project directory...");
    match env.discover_claude_project() {
        Ok(project_path) => {
            println!("\n✅ Found Claude project at: {:?}", project_path);
            
            // Extract the directory name to understand the pattern
            let dir_name = project_path.file_name().unwrap().to_string_lossy();
            println!("Directory name: {}", dir_name);
            
            // Find session file
            match env.find_session_file() {
                Ok(session_file) => {
                    println!("Session file: {:?}", session_file);
                    
                    // Print the mapping
                    println!("\n📝 DISCOVERED MAPPING:");
                    println!("Workspace path: {:?}", env.workspace);
                    println!("Claude project: {:?}", project_path);
                    println!("Pattern: {} -> {}", env.workspace.display(), dir_name);
                },
                Err(e) => println!("❌ Could not find session file: {}", e),
            }
        },
        Err(e) => {
            println!("❌ Could not discover Claude project: {}", e);
            
            // List all projects to help debug
            let claude_projects = std::path::PathBuf::from(std::env::var("HOME").unwrap())
                .join(".claude")
                .join("projects");
            
            println!("\nAll Claude projects:");
            if let Ok(entries) = std::fs::read_dir(&claude_projects) {
                for entry in entries {
                    if let Ok(entry) = entry {
                        println!("  - {}", entry.file_name().to_string_lossy());
                    }
                }
            }
        }
    }
    
    println!("\n=== Discovery Test Complete ===\n");
}