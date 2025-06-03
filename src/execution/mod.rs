pub mod executor;
pub mod observer;
pub mod recorder;  // Keep temporarily for Transition type
pub mod workspace;
pub mod conversation;

// Core types
pub use executor::{ClaudeExecutor, ClaudePrompt, ClaudeExecution, ExecutorError};
pub use observer::{EnvironmentObserver, EnvironmentSnapshot, ObserverError};
pub use recorder::Transition;  // Move this type out of recorder later
pub use workspace::{Workspace, WorkspaceError};
pub use conversation::{Conversation, ConversationError, ConversationMetadata};