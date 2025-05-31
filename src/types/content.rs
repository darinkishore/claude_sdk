use serde::{Deserialize, Deserializer, Serialize};
use serde::de::{self, Visitor, SeqAccess};

/// Different types of content within a message
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ContentBlock {
    #[serde(rename = "text")]
    Text { 
        text: String 
    },
    #[serde(rename = "thinking")]
    Thinking { 
        thinking: String, 
        signature: String 
    },
    #[serde(rename = "tool_use")]
    ToolUse { 
        id: String, 
        name: String, 
        input: serde_json::Value 
    },
    #[serde(rename = "tool_result")]
    ToolResult {
        #[serde(rename = "tool_use_id")]
        tool_use_id: String,
        #[serde(default, deserialize_with = "deserialize_optional_tool_result_content")]
        content: Option<ToolResultContent>,
        #[serde(rename = "is_error")]
        is_error: Option<bool>,
    },
    #[serde(rename = "image")]
    Image {
        #[serde(rename = "source")]
        source: ImageSource,
    },
}

/// Image source information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageSource {
    #[serde(rename = "type")]
    pub source_type: String, // Usually "base64"
    pub media_type: String, // e.g., "image/png", "image/jpeg"
    pub data: String, // Base64 encoded image data
}

/// Tool result content can be either a string or an array of content blocks
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ToolResultContent {
    Text(String),
    Blocks(Vec<ContentBlock>),
}

impl ToolResultContent {
    /// Get the text representation of the content
    pub fn as_text(&self) -> String {
        match self {
            ToolResultContent::Text(s) => s.clone(),
            ToolResultContent::Blocks(blocks) => {
                blocks.iter()
                    .filter_map(|block| match block {
                        ContentBlock::Text { text } => Some(text.as_str()),
                        _ => None,
                    })
                    .collect::<Vec<_>>()
                    .join("\n")
            }
        }
    }
}

/// Custom deserializer for optional tool result content that can be string or array
fn deserialize_optional_tool_result_content<'de, D>(deserializer: D) -> Result<Option<ToolResultContent>, D::Error>
where
    D: Deserializer<'de>,
{
    struct OptionalToolResultContentVisitor;
    
    impl<'de> Visitor<'de> for OptionalToolResultContentVisitor {
        type Value = Option<ToolResultContent>;
        
        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("optional string or array of content blocks")
        }
        
        fn visit_none<E>(self) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            Ok(None)
        }
        
        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: Deserializer<'de>,
        {
            deserializer.deserialize_any(ToolResultContentVisitor).map(Some)
        }
        
        fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            Ok(Some(ToolResultContent::Text(value.to_string())))
        }
        
        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let mut blocks = Vec::new();
            while let Some(block) = seq.next_element()? {
                blocks.push(block);
            }
            Ok(Some(ToolResultContent::Blocks(blocks)))
        }
    }
    
    struct ToolResultContentVisitor;
    
    impl<'de> Visitor<'de> for ToolResultContentVisitor {
        type Value = ToolResultContent;
        
        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("string or array of content blocks")
        }
        
        fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            Ok(ToolResultContent::Text(value.to_string()))
        }
        
        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let mut blocks = Vec::new();
            while let Some(block) = seq.next_element()? {
                blocks.push(block);
            }
            Ok(ToolResultContent::Blocks(blocks))
        }
    }
    
    deserializer.deserialize_option(OptionalToolResultContentVisitor)
}

/// Custom deserializer for message content field that can be string or array
pub fn deserialize_message_content<'de, D>(deserializer: D) -> Result<Vec<ContentBlock>, D::Error>
where
    D: Deserializer<'de>,
{
    struct ContentVisitor;
    
    impl<'de> Visitor<'de> for ContentVisitor {
        type Value = Vec<ContentBlock>;
        
        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("string or array of content blocks")
        }
        
        fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
        where
            E: de::Error,
        {
            Ok(vec![ContentBlock::Text { text: value.to_string() }])
        }
        
        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let mut blocks = Vec::new();
            while let Some(block) = seq.next_element()? {
                blocks.push(block);
            }
            Ok(blocks)
        }
    }
    
    deserializer.deserialize_any(ContentVisitor)
}