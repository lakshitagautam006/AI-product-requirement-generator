from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from src.agents.prompts import BA_PROMPT_TEMPLATE
from src.config import get_default_model, get_groq_api_key


def run_ba_analysis(
    product_name: str,
    product_idea: str,
    domain: str = "General Tech",
    constraints: str = "Standard web/mobile platform",
    rag_context: str = "",
    groq_api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.4
) -> str:
    """Execute the Business Analyst agent chain to generate problem statement and personas."""
    api_key = get_groq_api_key(groq_api_key)
    if not api_key:
        raise ValueError("Groq API key is missing. Please provide it in the UI or set GROQ_API_KEY in .env.")

    effective_model = model_name if model_name and model_name.strip() else get_default_model(api_key)

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=effective_model,
        temperature=temperature,
        max_tokens=4096
    )

    chain = BA_PROMPT_TEMPLATE | llm | StrOutputParser()

    response = chain.invoke({
        "product_name": product_name,
        "product_idea": product_idea,
        "domain": domain,
        "constraints": constraints,
        "rag_context": rag_context
    })

    return response
