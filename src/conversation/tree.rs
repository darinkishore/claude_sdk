use uuid::Uuid;
use std::collections::HashMap;

use crate::types::MessageRecord;
use crate::error::ParseError;

/// Represents a conversation as a tree structure
#[derive(Debug, Clone)]
pub struct ConversationTree {
    /// Root messages (no parent)
    pub root_messages: Vec<ConversationNode>,
    /// Messages with parent_uuid not found in session
    pub orphaned_messages: Vec<Uuid>,
    /// Detected circular parent-child relationships
    pub circular_references: Vec<(Uuid, Uuid)>,
}

/// A node in the conversation tree
#[derive(Debug, Clone)]
pub struct ConversationNode {
    pub message: MessageRecord,
    pub children: Vec<ConversationNode>,
}

impl ConversationTree {
    /// Build a conversation tree from a collection of messages
    pub fn from_messages(messages: Vec<MessageRecord>) -> Result<Self, ParseError> {
        if messages.is_empty() {
            return Ok(ConversationTree {
                root_messages: Vec::new(),
                orphaned_messages: Vec::new(),
                circular_references: Vec::new(),
            });
        }
        
        // Create a map of all message UUIDs for validation
        let all_uuids: std::collections::HashSet<Uuid> = messages.iter()
            .map(|m| m.uuid)
            .collect();
        
        // Track orphaned messages and circular references
        let mut orphaned_messages = Vec::new();
        let mut circular_references = Vec::new();
        
        // Detect circular references - iterative approach to avoid stack overflow
        fn has_circular_reference(
            start_uuid: Uuid, 
            messages_by_uuid: &HashMap<Uuid, MessageRecord>
        ) -> Option<Uuid> {
            let mut visited = std::collections::HashSet::new();
            let mut current = Some(start_uuid);
            
            while let Some(uuid) = current {
                if visited.contains(&uuid) {
                    return Some(uuid);
                }
                visited.insert(uuid);
                
                current = messages_by_uuid.get(&uuid)
                    .and_then(|msg| msg.parent_uuid);
            }
            None
        }
        
        // Create lookup map
        let messages_by_uuid: HashMap<Uuid, MessageRecord> = messages.iter()
            .map(|m| (m.uuid, m.clone()))
            .collect();
        
        // Group messages by parent_uuid
        let mut children_map: HashMap<Option<Uuid>, Vec<MessageRecord>> = HashMap::new();
        
        for message in messages {
            // Check for orphaned messages
            if let Some(parent_uuid) = message.parent_uuid {
                if !all_uuids.contains(&parent_uuid) {
                    orphaned_messages.push(message.uuid);
                    continue;
                }
                
                // Check for circular references
                if let Some(circular_uuid) = has_circular_reference(message.uuid, &messages_by_uuid) {
                    circular_references.push((message.uuid, circular_uuid));
                    continue;
                }
            }
            
            children_map
                .entry(message.parent_uuid)
                .or_insert_with(Vec::new)
                .push(message);
        }
        
        // Build tree starting from root messages (those with no parent)
        let root_messages = children_map
            .remove(&None)
            .unwrap_or_default()
            .into_iter()
            .map(|msg| ConversationNode::build_subtree(msg, &mut children_map))
            .collect::<Result<Vec<_>, _>>()?;
        
        Ok(ConversationTree { 
            root_messages,
            orphaned_messages,
            circular_references,
        })
    }
    
    /// Get all messages in the tree in chronological order
    pub fn all_messages(&self) -> Vec<&MessageRecord> {
        let mut messages = Vec::new();
        for root in &self.root_messages {
            root.collect_messages(&mut messages);
        }
        
        // Sort by timestamp
        messages.sort_by_key(|msg| msg.timestamp);
        messages
    }
    
    /// Get all leaf nodes (messages with no children)
    pub fn leaf_nodes(&self) -> Vec<&ConversationNode> {
        let mut leaves = Vec::new();
        for root in &self.root_messages {
            root.collect_leaves(&mut leaves);
        }
        leaves
    }
    
    /// Find the conversation path to a specific message UUID
    pub fn path_to_message(&self, target_uuid: Uuid) -> Option<Vec<&MessageRecord>> {
        for root in &self.root_messages {
            if let Some(path) = root.find_path_to(target_uuid) {
                return Some(path);
            }
        }
        None
    }
    
    /// Get conversation statistics
    pub fn stats(&self) -> ConversationStats {
        let all_messages = self.all_messages();
        let total_messages = all_messages.len();
        let max_depth = self.max_depth();
        let num_branches = self.count_branches();
        let leaf_count = self.leaf_nodes().len();
        
        ConversationStats {
            total_messages,
            max_depth,
            num_branches,
            leaf_count,
        }
    }
    
    /// Calculate the maximum depth of the conversation tree
    pub fn max_depth(&self) -> usize {
        self.root_messages
            .iter()
            .map(|root| root.depth())
            .max()
            .unwrap_or(0)
    }
    
    /// Count the number of branching points in the conversation
    pub fn count_branches(&self) -> usize {
        let mut branches = 0;
        for root in &self.root_messages {
            branches += root.count_branches();
        }
        branches
    }
}

impl ConversationNode {
    /// Build a subtree recursively
    fn build_subtree(
        message: MessageRecord,
        children_map: &mut HashMap<Option<Uuid>, Vec<MessageRecord>>,
    ) -> Result<Self, ParseError> {
        let message_uuid = message.uuid;
        let children = children_map
            .remove(&Some(message_uuid))
            .unwrap_or_default()
            .into_iter()
            .map(|child_msg| Self::build_subtree(child_msg, children_map))
            .collect::<Result<Vec<_>, _>>()?;
        
        Ok(ConversationNode { message, children })
    }
    
    /// Collect all messages in this subtree
    fn collect_messages<'a>(&'a self, messages: &mut Vec<&'a MessageRecord>) {
        messages.push(&self.message);
        for child in &self.children {
            child.collect_messages(messages);
        }
    }
    
    /// Collect all leaf nodes in this subtree
    fn collect_leaves<'a>(&'a self, leaves: &mut Vec<&'a ConversationNode>) {
        if self.children.is_empty() {
            leaves.push(self);
        } else {
            for child in &self.children {
                child.collect_leaves(leaves);
            }
        }
    }
    
    /// Find path to a specific message UUID
    fn find_path_to(&self, target_uuid: Uuid) -> Option<Vec<&MessageRecord>> {
        if self.message.uuid == target_uuid {
            return Some(vec![&self.message]);
        }
        
        for child in &self.children {
            if let Some(mut path) = child.find_path_to(target_uuid) {
                path.insert(0, &self.message);
                return Some(path);
            }
        }
        
        None
    }
    
    /// Calculate the depth of this subtree
    fn depth(&self) -> usize {
        if self.children.is_empty() {
            1
        } else {
            1 + self.children.iter().map(|child| child.depth()).max().unwrap_or(0)
        }
    }
    
    /// Count branching points in this subtree
    fn count_branches(&self) -> usize {
        let mut branches = if self.children.len() > 1 { 1 } else { 0 };
        for child in &self.children {
            branches += child.count_branches();
        }
        branches
    }
    
    /// Check if this node is a leaf (has no children)
    pub fn is_leaf(&self) -> bool {
        self.children.is_empty()
    }
    
    /// Get the number of children
    pub fn child_count(&self) -> usize {
        self.children.len()
    }
}

/// Statistics about a conversation tree
#[derive(Debug, Clone)]
pub struct ConversationStats {
    pub total_messages: usize,
    pub max_depth: usize,
    pub num_branches: usize,
    pub leaf_count: usize,
}