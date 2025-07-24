use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use tracing::{debug, error};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize)]
pub struct PineconeQuery {
    pub vector: Vec<f32>,
    pub top_k: u32,
    pub namespace: Option<String>,
    pub include_metadata: bool,
    pub include_values: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PineconeMatch {
    pub id: String,
    pub score: f32,
    pub values: Option<Vec<f32>>,
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PineconeQueryResponse {
    pub matches: Vec<PineconeMatch>,
    pub namespace: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SourceInfo {
    pub source_reference: String,
    pub title: String,
}

pub struct PineconeClient {
    client: Client,
    base_url: String,
    api_key: String,
}

impl PineconeClient {
    pub fn new() -> Result<Self> {
        let api_key = std::env::var("PINECONE_API_KEY")
            .map_err(|_| anyhow!("PINECONE_API_KEY environment variable not set"))?;
        
        let base_url = std::env::var("PINECONE_BASE_URL")
            .map_err(|_| anyhow!("PINECONE_BASE_URL environment variable not set"))?;

        let client = Client::new();

        Ok(Self {
            client,
            base_url,
            api_key,
        })
    }

    pub async fn query_index(
        &self,
        index_name: &str,
        query_vector: Vec<f32>,
        namespace: Option<String>,
        top_k: u32,
    ) -> Result<PineconeQueryResponse> {
        let query = PineconeQuery {
            vector: query_vector,
            top_k,
            namespace: namespace.clone(),
            include_metadata: true,
            include_values: false,
        };

        let url = format!("{}/query", self.base_url);
        
        debug!("Querying Pinecone index: {} with namespace: {:?}", index_name, namespace);

        let response = self
            .client
            .post(&url)
            .header("Api-Key", &self.api_key)
            .header("Content-Type", "application/json")
            .json(&query)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to send request to Pinecone: {}", e))?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            error!("Pinecone API error: {} - {}", status, error_text);
            return Err(anyhow!("Pinecone API error: {} - {}", status, error_text));
        }

        let pinecone_response: PineconeQueryResponse = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse Pinecone response: {}", e))?;

        debug!("Retrieved {} matches from Pinecone", pinecone_response.matches.len());

        Ok(pinecone_response)
    }

    pub fn extract_context_and_sources(&self, matches: &[PineconeMatch]) -> (String, Vec<SourceInfo>) {
        let mut context_parts = Vec::new();
        let mut sources = Vec::new();
        let mut seen_sources = std::collections::HashSet::new();

        for m in matches {
            if let Some(metadata) = &m.metadata {
                // Extract page content for context
                if let Some(page_content) = metadata.get("page_content") {
                    if let Some(content_str) = page_content.as_str() {
                        context_parts.push(content_str.to_string());
                    }
                }

                // Extract source information
                let source_reference = metadata
                    .get("source_reference")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown")
                    .to_string();

                let filename = metadata
                    .get("filename")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown")
                    .to_string();

                let title = metadata
                    .get("title")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Untitled")
                    .to_string();

                // Create unique identifier for deduplication
                let source_identifier = (source_reference.clone(), filename.clone(), title.clone());

                if !seen_sources.contains(&source_identifier) {
                    seen_sources.insert(source_identifier);
                    sources.push(SourceInfo {
                        source_reference,
                        title,
                    });
                }
            }
        }

        let context = context_parts.join(" ");
        
        (context, sources)
    }
}
