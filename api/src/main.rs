mod embedding_service;
mod pinecone_client;
mod gemini_client;
mod prompt_manager;
mod query_service;
mod constants;
mod guardrails;
mod metrics;

use axum::{
    extract::State,
    http::StatusCode,
    response::{Json, Sse, sse::Event},
    routing::{get, post},
    Router,
};
use futures::stream::{self, Stream};
use serde_json::json;
use std::sync::Arc;
use std::time::Duration;
use tokio_stream::StreamExt as _;
use tower::ServiceBuilder;
use tower_http::cors::CorsLayer;
use tracing::{error, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use query_service::{QueryRequest, QueryResponse, QueryService};

type AppState = Arc<QueryService>;

#[tokio::main]
async fn main() {
    // Load environment variables from .env file
    dotenv::dotenv().ok();

    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "aven_api=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Initialize the query service
    let query_service = match QueryService::new().await {
        Ok(service) => Arc::new(service),
        Err(e) => {
            error!("Failed to initialize query service: {}", e);
            std::process::exit(1);
        }
    };

    // Build the application with routes
    let app = Router::new()
        .route("/query", post(query_handler))
        .route("/query/stream", post(query_stream_handler))
        .route("/health", get(health_check))
        .route("/metrics", get(metrics_handler))
        .layer(
            ServiceBuilder::new()
                .layer(CorsLayer::permissive())
        )
        .with_state(query_service);

    // Start the server
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080")
        .await
        .expect("Failed to bind to address");

    info!("Server starting on http://0.0.0.0:8080");
    
    axum::serve(listener, app)
        .await
        .expect("Server failed to start");
}

async fn query_handler(
    State(query_service): State<AppState>,
    Json(request): Json<QueryRequest>,
) -> Result<Json<QueryResponse>, (StatusCode, Json<serde_json::Value>)> {
    info!("Received query request: {}", request.question);

    match query_service.query_pinecone(request).await {
        Ok(response) => {
            info!("Successfully processed query");
            Ok(Json(response))
        }
        Err(e) => {
            error!("Failed to process query: {}", e);
            Err((
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({
                    "error": "Failed to process query",
                    "message": e.to_string()
                })),
            ))
        }
    }
}

async fn query_stream_handler(
    State(query_service): State<AppState>,
    Json(request): Json<QueryRequest>,
) -> Sse<impl Stream<Item = Result<Event, std::convert::Infallible>>> {
    info!("Received streaming query request: {}", request.question);
    
    let stream = async_stream::stream! {
        // Send initial event to indicate processing started
        yield Ok(Event::default()
            .event("start")
            .data(json!({"status": "processing"}).to_string()));

        match query_service.query_pinecone(request).await {
            Ok(response) => {
                // Stream the response in chunks
                let answer = response.answer;
                let words: Vec<&str> = answer.split_whitespace().collect();
                let chunk_size = 3; // Send 3 words at a time
                
                for chunk in words.chunks(chunk_size) {
                    let chunk_text = chunk.join(" ");
                    yield Ok(Event::default()
                        .event("chunk")
                        .data(json!({"chunk": chunk_text}).to_string()));
                    
                    // Small delay to simulate realistic streaming
                    tokio::time::sleep(Duration::from_millis(50)).await;
                }
                
                // Send final event with complete response and sources
                yield Ok(Event::default()
                    .event("complete")
                    .data(json!({
                        "answer": answer,
                        "sources": response.sources,
                        "context": response.context,
                        "guardrail_triggered": response.guardrail_triggered
                    }).to_string()));
            }
            Err(e) => {
                error!("Failed to process streaming query: {}", e);
                yield Ok(Event::default()
                    .event("error")
                    .data(json!({
                        "error": "Failed to process query",
                        "message": e.to_string()
                    }).to_string()));
            }
        }
        
        // Send end event
        yield Ok(Event::default()
            .event("end")
            .data("{}"));
    };

    Sse::new(stream)
}

async fn health_check() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "aven-api"
    }))
}

async fn metrics_handler(
    State(query_service): State<AppState>,
) -> Json<serde_json::Value> {
    let metrics = query_service.get_metrics();
    Json(json!({
        "metrics": metrics,
        "summary": query_service.get_metrics_summary()
    }))
}
