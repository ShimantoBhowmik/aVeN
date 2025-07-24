use anyhow::{anyhow, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use tracing::{debug, error};

#[derive(Debug, Serialize, Deserialize)]
struct GeminiContent {
    parts: Vec<GeminiPart>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiPart {
    text: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiRequest {
    contents: Vec<GeminiContent>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiCandidate {
    content: GeminiContent,
}

#[derive(Debug, Serialize, Deserialize)]
struct GeminiResponse {
    candidates: Vec<GeminiCandidate>,
}

pub struct GeminiClient {
    client: Client,
    api_key: String,
    model: String,
}

impl GeminiClient {
    pub fn new() -> Result<Self> {
        let api_key = std::env::var("GEMINI_API_KEY")
            .map_err(|_| anyhow!("GEMINI_API_KEY environment variable not set"))?;

        let model = std::env::var("GEMINI_MODEL")
            .unwrap_or_else(|_| "gemini-pro".to_string());

        let client = Client::new();

        Ok(Self {
            client,
            api_key,
            model,
        })
    }

    pub async fn generate_content(&self, prompt: &str) -> Result<String> {
        let request = GeminiRequest {
            contents: vec![GeminiContent {
                parts: vec![GeminiPart {
                    text: prompt.to_string(),
                }],
            }],
        };

        let url = format!(
            "https://generativelanguage.googleapis.com/v1/models/{}:generateContent?key={}",
            self.model, self.api_key
        );

        debug!("Sending request to Gemini API with prompt length: {}", prompt.len());

        let response = self
            .client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .map_err(|e| anyhow!("Failed to send request to Gemini: {}", e))?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            error!("Gemini API error: {} - {}", status, error_text);
            return Err(anyhow!("Gemini API error: {} - {}", status, error_text));
        }

        let gemini_response: GeminiResponse = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse Gemini response: {}", e))?;

        if gemini_response.candidates.is_empty() {
            return Err(anyhow!("No candidates returned from Gemini"));
        }

        let candidate = &gemini_response.candidates[0];
        if candidate.content.parts.is_empty() {
            return Err(anyhow!("No parts in Gemini response"));
        }

        let response_text = &candidate.content.parts[0].text;
        debug!("Generated response with length: {}", response_text.len());

        Ok(response_text.clone())
    }
}
