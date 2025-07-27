use anyhow::Result;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

use crate::constants::{PINECONE_INDEX_NAME, PINECONE_NAMESPACE, SIMILARITY_TOP_K};
use crate::embedding_service::EmbeddingService;
use crate::pinecone_client::{PineconeClient, SourceInfo};
use crate::gemini_client::GeminiClient;
use crate::prompt_manager::PromptManager;
use crate::guardrails::{GuardrailEngine, GuardrailViolation};
use crate::metrics::{GuardrailMetrics, GuardrailMetricsCollector};

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryRequest {
    pub question: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryResponse {
    pub answer: String,
    pub sources: Vec<SourceInfo>,
    pub context: String,
    pub guardrail_triggered: Option<String>,
}

pub struct QueryService {
    embedding_service: EmbeddingService,
    pinecone_client: PineconeClient,
    gemini_client: GeminiClient,
    prompt_manager: PromptManager,
    guardrail_engine: GuardrailEngine,
    metrics_collector: GuardrailMetricsCollector,
}

impl QueryService {
    pub async fn new() -> Result<Self> {
        let embedding_service = EmbeddingService::new().await?;
        let pinecone_client = PineconeClient::new()?;
        let gemini_client = GeminiClient::new()?;
        let prompt_manager = PromptManager::new()?;
        let guardrail_engine = GuardrailEngine::new()?;
        let metrics_collector = GuardrailMetricsCollector::new();

        Ok(Self {
            embedding_service,
            pinecone_client,
            gemini_client,
            prompt_manager,
            guardrail_engine,
            metrics_collector,
        })
    }

    pub async fn query_pinecone(&self, request: QueryRequest) -> Result<QueryResponse> {
        info!("Processing query: {}", request.question);
        
        // Record the query in metrics
        self.metrics_collector.record_query();

        // Step 1: Check input guardrails
        let input_check = self.guardrail_engine.check_input_guardrails(&request.question);
        if input_check.blocked {
            warn!("Query blocked by input guardrails: {:?}", input_check.violation);
            
            let violation_type = match input_check.violation {
                Some(GuardrailViolation::PersonalData(_)) => "personal_data",
                Some(GuardrailViolation::FinancialAdvice(_)) => "financial_advice",
                Some(GuardrailViolation::LegalAdvice(_)) => "legal_advice",
                Some(GuardrailViolation::Toxicity(_)) => "toxicity",
                Some(GuardrailViolation::Fraud(_)) => "fraud",
                Some(GuardrailViolation::OffTopic(_)) => "off_topic",
                None => "unknown",
            };

            // Record the violation in metrics
            self.metrics_collector.record_violation(violation_type);

            return Ok(QueryResponse {
                answer: input_check.safe_response.unwrap_or_else(|| 
                    "I'm sorry, but I cannot process that request. Please contact support@aven.com for assistance.".to_string()
                ),
                sources: vec![],
                context: String::new(),
                guardrail_triggered: Some(violation_type.to_string()),
            });
        }

        // Step 2: Generate embedding for the query
        let query_embedding = self.embedding_service.encode(&request.question).await?;

        // Step 3: Query Pinecone for similar documents
        let pinecone_response = self
            .pinecone_client
            .query_index(
                PINECONE_INDEX_NAME,
                query_embedding,
                Some(PINECONE_NAMESPACE.to_string()),
                SIMILARITY_TOP_K as u32,
            )
            .await?;

        // Step 4: Extract context and sources from the results
        let (context, sources) = self
            .pinecone_client
            .extract_context_and_sources(&pinecone_response.matches);

        // Step 5: Format the prompt using the template
        let formatted_prompt = self.prompt_manager.format_aven_ai_prompt(
            &context,
            &request.question,
            &sources,
        );

        // Step 6: Generate answer using Gemini
        let mut answer = self.gemini_client.generate_content(&formatted_prompt).await?;

        // Step 7: Check output guardrails
        let output_check = self.guardrail_engine.check_output_guardrails(&answer);
        let mut guardrail_triggered = None;
        
        if output_check.blocked {
            warn!("Response blocked by output guardrails: {:?}", output_check.violation);
            
            let violation_type = match output_check.violation {
                Some(GuardrailViolation::PersonalData(_)) => "output_personal_data",
                Some(GuardrailViolation::FinancialAdvice(_)) => "output_financial_advice",
                Some(GuardrailViolation::LegalAdvice(_)) => "output_legal_advice",
                Some(GuardrailViolation::Toxicity(_)) => "output_toxicity",
                Some(GuardrailViolation::Fraud(_)) => "output_fraud",
                Some(GuardrailViolation::OffTopic(_)) => "output_off_topic",
                None => "output_unknown",
            };

            // Record the violation in metrics
            self.metrics_collector.record_violation(violation_type);

            answer = output_check.safe_response.unwrap_or_else(|| 
                "I apologize, but I cannot provide that information. Please contact support@aven.com for assistance with your inquiry.".to_string()
            );
            
            guardrail_triggered = Some(violation_type.to_string());
        }

        info!("Successfully generated response for query");

        Ok(QueryResponse {
            answer,
            sources,
            context,
            guardrail_triggered,
        })
    }

    pub fn get_metrics(&self) -> GuardrailMetrics {
        self.metrics_collector.get_metrics()
    }

    pub fn get_metrics_summary(&self) -> String {
        self.metrics_collector.get_metrics_summary()
    }
}
