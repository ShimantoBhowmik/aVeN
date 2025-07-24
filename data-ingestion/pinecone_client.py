import os
import torch
import dotenv
import re
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai
from prompts.prompt_manager import PromptTemplateManager

dotenv.load_dotenv()


class PineconeClient:

    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_client = Pinecone(api_key=self.api_key, environment="us-east-1")
        self.device = (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2").to(
            self.device
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L12-v2"
        )
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self.llm_model = genai.GenerativeModel("gemini-1.5-flash")

        # Initialize prompt template manager
        self.prompt_manager = PromptTemplateManager()

    def create_pinecone_index(self, index_name):
        if index_name not in self.pinecone_client.list_indexes().names():
            self.pinecone_client.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

    def get_indexes(self):
        return self.pinecone_client.list_indexes().names()

    def get_namespaces(self, index_name):
        index_details = self.pinecone_client.Index(index_name).describe_index_stats()
        namespace_names = list(index_details["namespaces"].keys())
        return namespace_names

    def delete_pinecone_index(self, index_name):
        return self.pinecone_client.delete_index(index_name)

    def store_embeddings(self, index_name, namespace, document_name, texts):
        index = self.pinecone_client.Index(index_name)
        embeddings = self.model.encode([t.page_content for t in texts]).tolist()

        vectors = []
        for i, (embedding, t) in enumerate(zip(embeddings, texts)):
            vector = {
                "id": f"{document_name}_{i}",
                "values": embedding,
                "metadata": {
                    "document_name": document_name,
                    "text": t.page_content,
                    "source_type": t.metadata.get("source_type", "unknown"),
                    "source_reference": t.metadata.get("source_reference", "unknown"),
                    "title": t.metadata.get("title", "Untitled"),
                    "filename": t.metadata.get("filename", "unknown"),
                    "chunk_index": t.metadata.get("chunk_index", i),
                },
            }
            vectors.append(vector)

        index.upsert(vectors=vectors, namespace=namespace)

    def query_pinecone(self, index_name, namespace, query_text):
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=index_name, embedding=self.embeddings
        )
        docs = vectorstore.similarity_search(query_text, k=3, namespace=namespace)

        # Extract context and sources
        context = " ".join([doc.page_content for doc in docs])
        sources = []
        seen_sources = set()  # Track unique sources by reference and filename

        for doc in docs:
            source_info = {
                "source_type": doc.metadata.get("source_type", "unknown"),
                "source_reference": doc.metadata.get("source_reference", "unknown"),
                "title": doc.metadata.get("title", "Untitled"),
                "filename": doc.metadata.get("filename", "unknown"),
                "chunk_index": doc.metadata.get("chunk_index", 0),
            }

            # Create a unique identifier for the source
            source_identifier = (
                source_info["source_reference"],
                source_info["filename"],
                source_info["title"],
            )

            # Only add if we haven't seen this source before
            if source_identifier not in seen_sources:
                seen_sources.add(source_identifier)
                # Remove chunk_index from the final source info since we're deduplicating
                source_info_clean = {
                    "source_reference": source_info["source_reference"],
                    "title": source_info["title"],
                }
                sources.append(source_info_clean)

        # Generate answer with context using AvenAI prompt template
        formatted_prompt = self.prompt_manager.format_aven_ai_prompt(
            context=context, question=query_text, sources=sources
        )
        response = self.llm_model.generate_content(formatted_prompt)

        return {"answer": response.text, "sources": sources, "context": context}
