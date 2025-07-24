#!/bin/bash

# Test script for the Aven Rust API

BASE_URL="http://localhost:8080"

echo "Testing Aven Rust API..."
echo "========================"

# Test health endpoint
echo "1. Testing health endpoint..."
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n\n"

# Test query endpoint
echo "2. Testing query endpoint..."
curl -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the benefits of using an Aven credit card?"
  }' \
  -w "\nStatus: %{http_code}\n\n"

echo "Test completed!"
