import os
import shutil
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_huggingface import HuggingFaceEmbeddings

from src.config import KNOWLEDGE_BASE_DIR, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME

# Global cached embeddings and store
_embeddings_instance = None
_vector_store_instance = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Initialize or return cached HuggingFace embeddings."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings_instance


def load_knowledge_base_documents() -> List[Document]:
    """Read all markdown and text files from the knowledge base directory."""
    documents = []
    if not KNOWLEDGE_BASE_DIR.exists():
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        return documents

    for file_path in KNOWLEDGE_BASE_DIR.glob("*.*"):
        if file_path.suffix.lower() in [".md", ".txt"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                doc = Document(
                    page_content=content,
                    metadata={"source": file_path.name, "path": str(file_path)}
                )
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
    return documents


def initialize_vector_store(force_reload: bool = False) -> Chroma:
    """Build or load the Chroma vector database from the knowledge base."""
    global _vector_store_instance

    if _vector_store_instance is not None and not force_reload:
        return _vector_store_instance

    embeddings = get_embeddings()

    # If force reload requested, clean existing persist directory
    if force_reload and CHROMA_PERSIST_DIR.exists():
        shutil.rmtree(CHROMA_PERSIST_DIR, ignore_errors=True)

    # Check if a populated chroma db already exists
    if CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir()):
        try:
            _vector_store_instance = Chroma(
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=embeddings
            )
            return _vector_store_instance
        except Exception as e:
            print(f"Error loading existing Chroma DB: {e}. Rebuilding...")

    # Load and chunk documents
    docs = load_knowledge_base_documents()
    if not docs:
        # Fallback dummy document if no documents found
        docs = [
            Document(
                page_content="Standard PRD includes Problem Statement, Personas, User Stories, Functional & Non-Functional Requirements, and Risk Matrix.",
                metadata={"source": "default_standards"}
            )
        ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunked_docs = text_splitter.split_documents(docs)

    # Create Chroma vector store
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    _vector_store_instance = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR)
    )

    return _vector_store_instance
