use anyhow::{anyhow, Result};
use serde_json::json;
use std::collections::HashMap;
use crate::pinecone_client::SourceInfo;

pub struct PromptManager {
    aven_ai_template: String,
}

impl PromptManager {
    pub fn new() -> Result<Self> {
        let template = include_str!("../../prompts/aven_ai_prompt.txt");
        
        Ok(Self {
            aven_ai_template: template.to_string(),
        })
    }

    pub fn format_aven_ai_prompt(
        &self,
        context: &str,
        question: &str,
        sources: &[SourceInfo],
    ) -> String {
        let sources_formatted = self.format_sources(sources);
        
        self.aven_ai_template
            .replace("{context}", context)
            .replace("{question}", question)
            .replace("{sources}", &sources_formatted)
    }

    fn format_sources(&self, sources: &[SourceInfo]) -> String {
        if sources.is_empty() {
            return "No sources available.".to_string();
        }

        sources
            .iter()
            .enumerate()
            .map(|(i, source)| {
                format!(
                    "{}. **{}** (Reference: {})",
                    i + 1,
                    source.title,
                    source.source_reference
                )
            })
            .collect::<Vec<String>>()
            .join("\n")
    }
}
