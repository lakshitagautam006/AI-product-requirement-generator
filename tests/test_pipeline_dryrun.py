"""Test module imports and prompt construction."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import DEFAULT_GROQ_MODEL, AVAILABLE_GROQ_MODELS
from src.rag.vector_store import initialize_vector_store
from src.rag.retriever import retrieve_relevant_guidelines
from src.agents.prompts import BA_PROMPT_TEMPLATE, PM_PROMPT_TEMPLATE
from src.utils.export_utils import sanitize_filename, extract_sections


def test_dryrun():
    print("1. Checking config...")
    assert DEFAULT_GROQ_MODEL in AVAILABLE_GROQ_MODELS
    print(f"Default model: {DEFAULT_GROQ_MODEL}")

    print("\n2. Checking Vector DB and Retriever...")
    vs = initialize_vector_store()
    assert vs is not None
    guidelines = retrieve_relevant_guidelines("user stories functional requirements", k=2)
    assert len(guidelines) > 0
    print("Retrieved guidelines sample length:", len(guidelines))

    print("\n3. Testing prompt template formatting...")
    ba_prompt = BA_PROMPT_TEMPLATE.format_messages(
        product_name="TestApp",
        product_idea="Test product idea",
        domain="EdTech",
        constraints="None",
        rag_context=guidelines
    )
    assert len(ba_prompt) == 2
    print("BA prompt formatted successfully.")

    pm_prompt = PM_PROMPT_TEMPLATE.format_messages(
        product_name="TestApp",
        ba_output="# BA Output Sample",
        rag_context=guidelines
    )
    assert len(pm_prompt) == 2
    print("PM prompt formatted successfully.")

    print("\n4. Testing export and section parsing utilities...")
    dummy_prd = """# Product Requirement Document: TestApp
# 1. Executive Summary
This is a test summary.
# 2. Problem Statement
This is the problem statement.
# 3. User Personas
Persona 1: Student.
# 4. Scope & Boundaries
In scope: MVP.
# 5. User Stories
As a user I want login so that I access data.
# 6. Functional Requirements
| Req ID | Module |
# 7. Non-Functional Requirements
Latency < 200ms.
# 8. Risk Assessment Matrix
Risk 1: LLM latency.
"""
    clean_name = sanitize_filename("QuickBite Campus!")
    assert clean_name == "quickbite_campus"
    sections = extract_sections(dummy_prd)
    assert "Executive Summary" in sections
    assert "Problem Statement" in sections
    assert "User Stories" in sections
    print("Filename & section extraction verified.")

    print("\n[SUCCESS] Dry-run pipeline verification passed cleanly!")


if __name__ == "__main__":
    test_dryrun()
