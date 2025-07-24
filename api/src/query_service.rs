use anyhow::Result;
use serde::{Deserialize, Serialize};
use tracing::info;

use crate::constants::{PINECONE_INDEX_NAME, PINECONE_NAMESPACE, SIMILARITY_TOP_K};
use crate::embedding_service::EmbeddingService;
use crate::pinecone_client::{PineconeClient, SourceInfo};
use crate::gemini_client::GeminiClient;
use crate::prompt_manager::PromptManager;

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryRequest {
    pub question: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryResponse {
    pub answer: String,
    pub sources: Vec<SourceInfo>,
    pub context: String,
}

pub struct QueryService {
    embedding_service: EmbeddingService,
    pinecone_client: PineconeClient,
    gemini_client: GeminiClient,
    prompt_manager: PromptManager,
}

impl QueryService {
    pub async fn new() -> Result<Self> {
        let embedding_service = EmbeddingService::new().await?;
        let pinecone_client = PineconeClient::new()?;
        let gemini_client = GeminiClient::new()?;
        let prompt_manager = PromptManager::new()?;

        Ok(Self {
            embedding_service,
            pinecone_client,
            gemini_client,
            prompt_manager,
        })
    }

    pub async fn query_pinecone(&self, request: QueryRequest) -> Result<QueryResponse> {
        info!("Processing query: {}", request.question);

        // 1. Generate embedding for the query
        let query_embedding = self.embedding_service.encode(&request.question).await?;

        // 2. Query Pinecone for similar documents
        let pinecone_response = self
            .pinecone_client
            .query_index(
                PINECONE_INDEX_NAME,
                query_embedding,
                Some(PINECONE_NAMESPACE.to_string()),
                SIMILARITY_TOP_K as u32,
            )
            .await?;

        // 3. Extract context and sources from the results
        let (context, sources) = self
            .pinecone_client
            .extract_context_and_sources(&pinecone_response.matches);

        // 4. Format the prompt using the template
        let formatted_prompt = self.prompt_manager.format_aven_ai_prompt(
            &context,
            &request.question,
            &sources,
        );

        // 5. Generate answer using Gemini
        let answer = self.gemini_client.generate_content(&formatted_prompt).await?;

        info!("Successfully generated response for query");

        Ok(QueryResponse {
            answer,
            sources,
            context,
        })
    }
}
