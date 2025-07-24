mod embedding_service;
mod pinecone_client;
mod gemini_client;
mod prompt_manager;
mod query_service;
mod constants;

use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::post,
    Router,
};
use serde_json::json;
use std::sync::Arc;
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
        .route("/health", axum::routing::get(health_check))
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

async fn health_check() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "aven-api"
    }))
}
