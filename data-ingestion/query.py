#!/usr/bin/env python3
"""
Simple query script for the Aven Knowledge Base
"""

import os
import sys
import dotenv
from knowledge_base_processor import KnowledgeBaseProcessor

# Load environment variables
dotenv.load_dotenv()


def main():
    """Interactive query interface"""
    print("=" * 60)
    print("Aven Knowledge Base Query Interface")
    print("=" * 60)
    print("Type 'quit' or 'exit' to stop")
    print("-" * 60)

    processor = KnowledgeBaseProcessor()

    while True:
        try:
            question = input("\nEnter your question: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not question:
                continue

            print("\nSearching knowledge base...")
            result = processor.query_with_source(question)

            if result.get("error"):
                print(f"Error: {result['error']}")
                continue

            print("\n" + "=" * 50)
            print("ANSWER")
            print("=" * 50)
            print(result["answer"])

            print("\n" + "=" * 50)
            print("SOURCES")
            print("=" * 50)

            if result["sources"]:
                for i, source in enumerate(result["sources"], 1):
                    print(f"{i}. {source['title']}")
                    if source["source_type"] == "pdf" or source["source_type"] == "web":
                        print(f"{source['source_reference']}")
                    print()
            else:
                print("No sources found")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
