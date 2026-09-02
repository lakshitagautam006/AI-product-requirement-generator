from typing import List
from src.rag.vector_store import initialize_vector_store


def retrieve_relevant_guidelines(query: str, k: int = 3) -> str:
    """Retrieve top-k relevant PRD and engineering guideline chunks for a query."""
    try:
        vector_store = initialize_vector_store()
        results = vector_store.similarity_search(query, k=k)
        if not results:
            return "Standard industry PRD practices apply."

        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "knowledge_base")
            context_parts.append(f"[Guideline Ref {i} from {source}]:\n{doc.page_content.strip()}")

        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"Warning: RAG retrieval failed with error: {e}. Using fallback.")
        return "Ensure high clarity, INVEST user stories, standard NFR metrics (latency, security, availability), and risk mitigations."
