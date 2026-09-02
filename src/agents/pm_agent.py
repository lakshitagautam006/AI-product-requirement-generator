from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from src.agents.prompts import PM_PROMPT_TEMPLATE
from src.config import get_default_model, get_groq_api_key


def run_pm_specification(
    product_name: str,
    ba_output: str,
    rag_context: str = "",
    groq_api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.3
) -> str:
    """Execute the Product Manager agent chain to generate user stories, functional/non-functional specs, and risks."""
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

    chain = PM_PROMPT_TEMPLATE | llm | StrOutputParser()

    response = chain.invoke({
        "product_name": product_name,
        "ba_output": ba_output,
        "rag_context": rag_context
    })

    return response
