from typing import Callable, Dict, Any, Optional
from datetime import datetime
from src.rag.retriever import retrieve_relevant_guidelines
from src.agents.ba_agent import run_ba_analysis
from src.agents.pm_agent import run_pm_specification
from src.config import get_default_model, get_groq_api_key


def generate_full_prd(
    product_name: str,
    product_idea: str,
    domain: str = "General Tech",
    constraints: str = "Standard web/mobile platform",
    groq_api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, Any]:
    """
    Orchestrate the full multi-agent PRD generation pipeline.

    Workflow:
    1. Retrieve BA Domain Guidelines via RAG.
    2. Run Business Analyst Agent (Problem Statement, Personas, Scope).
    3. Retrieve NFR & Risk Assessment Frameworks via RAG.
    4. Run Product Manager Agent (User Stories, Functional Specs, NFRs, Risks).
    5. Assemble full PRD and return structured dictionary.
    """

    def notify(msg: str, progress: float):
        if progress_callback:
            progress_callback(msg, progress)

    # Resolve active API key and consistent model name
    resolved_key = get_groq_api_key(groq_api_key)
    effective_model = model_name if model_name and model_name.strip() else get_default_model(resolved_key)

    # Step 1: RAG retrieval for Business Analyst
    notify("🔍 Step 1/4: Querying Knowledge Base for PRD Standards & Personas...", 0.15)
    ba_rag_query = f"PRD structure problem statement user personas guidelines for {domain} {product_idea}"
    ba_rag_context = retrieve_relevant_guidelines(ba_rag_query, k=2)

    # Step 2: Run BA Agent
    notify(f"💼 Step 2/4: Running Business Analyst Agent using `{effective_model}`...", 0.40)
    ba_output = run_ba_analysis(
        product_name=product_name,
        product_idea=product_idea,
        domain=domain,
        constraints=constraints,
        rag_context=ba_rag_context,
        groq_api_key=resolved_key,
        model_name=effective_model
    )

    # Step 3: RAG retrieval for Product Manager
    notify("📚 Step 3/4: Querying Knowledge Base for Technical NFRs & Risk Matrices...", 0.65)
    pm_rag_query = f"Non-functional requirements security latency reliability risk matrix for {domain}"
    pm_rag_context = retrieve_relevant_guidelines(pm_rag_query, k=2)

    # Step 4: Run PM Agent
    notify(f"⚙️ Step 4/4: Running Product Manager Agent using `{effective_model}`...", 0.85)
    pm_output = run_pm_specification(
        product_name=product_name,
        ba_output=ba_output,
        rag_context=pm_rag_context,
        groq_api_key=resolved_key,
        model_name=effective_model
    )

    notify("✅ Finalizing Complete Product Requirement Document...", 1.0)

    # Assemble Document Header
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    document_header = f"""# Product Requirement Document (PRD): {product_name}

**Domain / Industry**: {domain}  
**Generated Date**: {timestamp_str}  
**Architecture Pipeline**: LangChain Dual-Agent (BA + PM) with RAG Vector Store (Groq `{effective_model}`)  
**Status**: Draft v1.0  

---
"""

    full_prd_markdown = f"{document_header}\n\n{ba_output}\n\n---\n\n{pm_output}"

    return {
        "product_name": product_name,
        "domain": domain,
        "model_used": effective_model,
        "ba_output": ba_output,
        "pm_output": pm_output,
        "full_prd": full_prd_markdown,
        "ba_rag_context": ba_rag_context,
        "pm_rag_context": pm_rag_context
    }
