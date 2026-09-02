"""Quick test script to verify RAG vector store and ChromaDB retrieval."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rag.vector_store import initialize_vector_store
from src.rag.retriever import retrieve_relevant_guidelines


def test_rag():
    print("1. Initializing Chroma Vector Store...")
    vs = initialize_vector_store(force_reload=False)
    print("Vector Store initialized successfully.")

    print("\n2. Testing semantic retrieval...")
    query = "Non-functional requirements security and performance latency"
    results = retrieve_relevant_guidelines(query, k=2)
    print(f"Retrieval Query: {query}")
    print("--- Retrieved Context ---")
    print(results)
    print("--- End Context ---")
    assert len(results) > 0, "Retrieved context should not be empty."
    print("\n[SUCCESS] RAG test passed successfully!")


if __name__ == "__main__":
    test_rag()
