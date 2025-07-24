use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use tracing::{debug, error};

#[derive(Debug, Serialize, Deserialize)]
struct HuggingFaceRequest {
    inputs: Vec<String>,
    options: Option<HuggingFaceOptions>,
}

#[derive(Debug, Serialize, Deserialize)]
struct HuggingFaceOptions {
    wait_for_model: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct HuggingFaceResponse(Vec<Vec<f32>>);

pub struct EmbeddingService {
    client: Client,
    model_url: String,
    api_token: String,
}

impl EmbeddingService {
    pub async fn new() -> Result<Self> {
        let api_token = std::env::var("HUGGINGFACE_API_TOKEN")
            .map_err(|_| anyhow!("HUGGINGFACE_API_TOKEN environment variable not set"))?;

        let model_url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction".to_string();

        let client = Client::new();

        Ok(Self {
            client,
            model_url,
            api_token,
        })
    }

    pub async fn encode(&self, text: &str) -> Result<Vec<f32>> {
        let request_body = json!({
            "inputs": [text]
        });

        debug!("Generating embedding for text of length: {}", text.len());

        let response = self
            .client
            .post(&self.model_url)
            .header("Authorization", format!("Bearer {}", self.api_token))
            .header("Content-Type", "application/json")
            .json(&request_body)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to send request to HuggingFace: {}", e))?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            error!("HuggingFace API error: {} - {}", status, error_text);
            return Err(anyhow!("HuggingFace API error: {} - {}", status, error_text));
        }

        let huggingface_response: HuggingFaceResponse = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse HuggingFace response: {}", e))?;

        if huggingface_response.0.is_empty() {
            return Err(anyhow!("No embeddings returned from HuggingFace"));
        }

        let embedding = huggingface_response.0[0].clone();
        debug!("Generated embedding with {} dimensions", embedding.len());

        Ok(embedding)
    }
}
