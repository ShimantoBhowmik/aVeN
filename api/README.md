# Aven Rust API

A Rust-based API service that integrates Pinecone vector search with Gemini AI to provide contextual responses using the AvenAI template.

## Features

- **Vector Search**: Queries Pinecone for similar documents using HuggingFace embeddings
- **AI Response Generation**: Uses Google Gemini to generate responses based on retrieved context
- **Source Citation**: Automatically extracts and deduplicates sources from search results
- **RESTful API**: Provides HTTP endpoints for querying the system

## Setup

### Prerequisites

- Rust (1.70+)
- API Keys for:
  - HuggingFace (for embeddings)
  - Pinecone (for vector search)
  - Google Gemini (for response generation)

### Installation

1. Clone the repository and navigate to the rust-api directory:
   ```bash
   cd rust-api
   ```

2. Copy the environment template and fill in your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

3. Build the project:
   ```bash
   cargo build --release
   ```

4. Run the server:
   ```bash
   cargo run
   ```

The server will start on `http://0.0.0.0:8080`

## API Endpoints

### POST /query

Query the knowledge base and get an AI-generated response.

**Request Body:**
```json
{
    "question": "What are Aven's credit card benefits?",
    "index_name": "aven-knowledge-base",
    "namespace": "main"
}
```

**Response:**
```json
{
    "answer": "Based on the available information...",
    "sources": [
        {
            "source_reference": "https://example.com/page",
            "title": "Aven Credit Card Benefits"
        }
    ],
    "context": "Retrieved context from vector search..."
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "aven-api"
}
```

## Environment Variables

- `HUGGINGFACE_API_TOKEN`: Your HuggingFace API token
- `PINECONE_API_KEY`: Your Pinecone API key  
- `PINECONE_BASE_URL`: Your Pinecone index URL
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_MODEL`: Gemini model to use (default: "gemini-pro")
- `RUST_LOG`: Logging level (default: "aven_api=debug,tower_http=debug")

## Architecture

The service consists of several modules:

- **embedding_service**: Generates embeddings using HuggingFace
- **pinecone_client**: Handles vector search queries to Pinecone
- **gemini_client**: Integrates with Google Gemini for response generation
- **prompt_manager**: Formats prompts using the AvenAI template
- **query_service**: Orchestrates the entire query pipeline

## Usage Example

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I apply for an Aven credit card?",
    "index_name": "aven-knowledge-base", 
    "namespace": "main"
  }'
```
