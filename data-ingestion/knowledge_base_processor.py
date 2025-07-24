#!/usr/bin/env python3
"""
Knowledge Base Processor
Processes all files in the knowledge-base folder and stores them in Pinecone with source tracking
"""

import os
import sys
import re
import dotenv
from typing import List, Dict, Any, Tuple
from pinecone_client import PineconeClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Load environment variables
dotenv.load_dotenv()


class KnowledgeBaseProcessor:
    """Processes knowledge base files and stores them in Pinecone with source tracking"""

    def __init__(self, knowledge_base_folder: str = "../knowledge-base"):
        self.knowledge_base_folder = knowledge_base_folder
        self.pinecone_client = PineconeClient()
        self.index_name = os.getenv("INDEX_NAME", "aven-knowledge-base")
        self.namespace = "aven-knowledge-base"

        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def extract_source_info(self, filename: str, content: str) -> Tuple[str, str]:
        """
        Extract source information from filename and content

        Args:
            filename: Name of the file
            content: Content of the file

        Returns:
            Tuple of (source_type, source_url_or_name)
        """
        if filename.startswith("PDF_"):
            # First try to extract URL from PDF content (PDFs now have URLs too)
            url_match = re.search(r"URL: (https?://[^\n]+)", content)
            if url_match:
                return "pdf", url_match.group(1)
            else:
                # Fallback: Extract PDF name from filename like PDF_Aven-CFPBHELOCBooklet_6d37cdde.txt
                pdf_match = re.match(r"PDF_(.+?)_[a-f0-9]+\.txt", filename)
                if pdf_match:
                    pdf_name = pdf_match.group(1)
                    return "pdf", f"{pdf_name}.pdf"
                else:
                    return "pdf", filename
        else:
            # Extract URL from web content
            url_match = re.search(r"URL: (https?://[^\n]+)", content)
            if url_match:
                return "web", url_match.group(1)
            else:
                return "web", filename

    def extract_title(self, content: str) -> str:
        """Extract title from content"""
        title_match = re.search(r"Title: ([^\n]+)", content)
        if title_match:
            return title_match.group(1)

        # If no title found, try to get first line of actual content
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if (
                line
                and not line.startswith("URL:")
                and not line.startswith("Title:")
                and line != "=" * 50
            ):
                return line[:100] + "..." if len(line) > 100 else line

        return "Untitled Document"

    def clean_content(self, content: str) -> str:
        """Clean content by removing metadata headers"""
        # Remove URL and Title lines
        content = re.sub(r"URL: https?://[^\n]+\n", "", content)
        content = re.sub(r"Title: [^\n]+\n", "", content)
        content = re.sub(r"Source PDF: [^\n]+\n", "", content)

        # Remove separator lines
        content = re.sub(r"=+\n", "", content)

        # Remove page markers for PDFs
        content = re.sub(r"--- Page \d+ ---\n", "", content)

        # Clean up extra whitespace
        content = re.sub(r"\n\s*\n", "\n\n", content)
        content = content.strip()

        return content

    def process_file(self, filepath: str) -> List[Document]:
        """
        Process a single file and return list of Document chunks

        Args:
            filepath: Path to the file to process

        Returns:
            List of Document objects with content and metadata
        """
        filename = os.path.basename(filepath)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return []

        # Extract source information
        source_type, source_reference = self.extract_source_info(filename, content)
        title = self.extract_title(content)

        # Clean content
        cleaned_content = self.clean_content(content)

        if not cleaned_content.strip():
            print(f"Warning: No content found in {filename}")
            return []

        # Split content into chunks
        chunks = self.text_splitter.split_text(cleaned_content)

        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "source_type": source_type,
                "source_reference": source_reference,
                "title": title,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }

            documents.append(Document(page_content=chunk, metadata=metadata))

        return documents

    def process_all_files(self) -> Dict[str, Any]:
        """
        Process all files in the knowledge base folder

        Returns:
            Dictionary with processing results
        """
        if not os.path.exists(self.knowledge_base_folder):
            raise FileNotFoundError(
                f"Knowledge base folder not found: {self.knowledge_base_folder}"
            )

        # Get all .txt files
        txt_files = [
            f for f in os.listdir(self.knowledge_base_folder) if f.endswith(".txt")
        ]

        if not txt_files:
            print(f"No .txt files found in {self.knowledge_base_folder}")
            return {"successful": 0, "failed": 0, "total_chunks": 0, "errors": []}

        print(f"Found {len(txt_files)} files to process")

        # Create Pinecone index if it doesn't exist
        print(f"Creating/checking Pinecone index: {self.index_name}")
        self.pinecone_client.create_pinecone_index(self.index_name)

        # Process all files
        all_documents = []
        successful = 0
        failed = 0
        errors = []

        for filename in txt_files:
            filepath = os.path.join(self.knowledge_base_folder, filename)
            print(f"Processing: {filename}")

            try:
                documents = self.process_file(filepath)
                if documents:
                    all_documents.extend(documents)
                    successful += 1
                    print(f"  ✓ Created {len(documents)} chunks")
                else:
                    failed += 1
                    errors.append(f"No content extracted from {filename}")
                    print(f"  ✗ No content extracted")
            except Exception as e:
                failed += 1
                errors.append(f"Error processing {filename}: {str(e)}")
                print(f"  ✗ Error: {e}")

        # Store all documents in Pinecone
        if all_documents:
            print(f"\nStoring {len(all_documents)} chunks in Pinecone...")
            try:
                self.pinecone_client.store_embeddings(
                    self.index_name, self.namespace, "knowledge_base", all_documents
                )
                print("✓ Successfully stored all embeddings in Pinecone")
            except Exception as e:
                errors.append(f"Error storing embeddings: {str(e)}")
                print(f"✗ Error storing embeddings: {e}")

        return {
            "successful": successful,
            "failed": failed,
            "total_chunks": len(all_documents),
            "errors": errors,
        }

    def query_with_source(self, query_text: str, k: int = 3) -> Dict[str, Any]:
        """
        Query the knowledge base and return results with source information

        Args:
            query_text: The question to ask
            k: Number of relevant chunks to retrieve

        Returns:
            Dictionary with answer and source information
        """
        try:
            # Query Pinecone
            result = self.pinecone_client.query_pinecone(
                self.index_name, self.namespace, query_text
            )

            return result

        except Exception as e:
            return {
                "error": f"Error querying knowledge base: {str(e)}",
                "answer": None,
                "sources": None,
            }


def main():
    """Main function to process knowledge base"""
    import argparse

    parser = argparse.ArgumentParser(description="Aven Knowledge Base Processor")
    parser.add_argument(
        "--test", action="store_true", help="Test queries after processing"
    )
    parser.add_argument(
        "--query-only",
        action="store_true",
        help="Only run test queries, skip processing",
    )
    args = parser.parse_args()

    if args.query_only:
        test_query()
        return

    print("=" * 60)
    print("Aven Knowledge Base Processor")
    print("=" * 60)

    processor = KnowledgeBaseProcessor()

    try:
        results = processor.process_all_files()

        print("\n" + "=" * 60)
        print("PROCESSING RESULTS")
        print("=" * 60)
        print(f"Files processed successfully: {results['successful']}")
        print(f"Files failed: {results['failed']}")
        print(f"Total chunks created: {results['total_chunks']}")

        if results["errors"]:
            print(f"\nErrors encountered:")
            for error in results["errors"]:
                print(f"  • {error}")

        if results["successful"] > 0:
            print(f"\n✓ Knowledge base successfully processed and stored in Pinecone!")
            print(f"Index: {processor.index_name}")
            print(f"Namespace: {processor.namespace}")

            if args.test:
                test_query()
        else:
            print(f"\n✗ No files were successfully processed")

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


def test_query():
    """Test function to demonstrate querying with sources"""
    print("\n" + "=" * 60)
    print("TESTING QUERY WITH SOURCES")
    print("=" * 60)

    processor = KnowledgeBaseProcessor()

    test_questions = [
        "What is Aven?",
        "What services does Aven provide?",
        "How do HELOC loans work?",
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 40)

        result = processor.query_with_source(question)

        if result.get("error"):
            print(f"Error: {result['error']}")
            continue

        print(f"Answer: {result['answer']}")
        print("\nSources:")
        for i, source in enumerate(result["sources"], 1):
            if source["source_type"] == "pdf" or source["source_type"] == "web":
                print(f"     Source: {source['source_reference']}")


if __name__ == "__main__":
    main()
    test_query()
