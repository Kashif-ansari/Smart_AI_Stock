"""Local FAISS retrieval and Groq advice generation for SmartStock AI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"
FAISS_INDEX_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "inventory_faiss"


def build_inventory_knowledge_base(sales_summary_df: pd.DataFrame, stock_df: pd.DataFrame) -> Any:
    """Build and persist a local FAISS store from sales and stock snapshots.

    The returned LangChain ``FAISS`` object can be supplied directly to
    :func:`query_smart_inventory_rag`. The index is also written to
    ``data/inventory_faiss`` so the latest snapshot is available locally.
    """
    _validate_dataframe(sales_summary_df, "sales_summary_df")
    _validate_dataframe(stock_df, "stock_df")
    combined = _combine_inventory_data(sales_summary_df, stock_df)
    if combined.empty:
        raise ValueError("Cannot build an inventory knowledge base from empty data.")

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
    except ImportError as exc:
        raise ImportError("Install langchain-community, faiss-cpu, and sentence-transformers to use RAG.") from exc

    documents = [
        Document(
            page_content=_format_product_document(row),
            metadata={
                "product_id": str(row["product_id"]),
                "product_name": str(row["product_name"]),
                "category": str(row["category"]),
                "reorder_recommended": bool(row["reorder_recommended"]),
            },
        )
        for _, row in combined.iterrows()
    ]
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    faiss_store = FAISS.from_documents(documents, embeddings)
    FAISS_INDEX_DIRECTORY.parent.mkdir(parents=True, exist_ok=True)
    faiss_store.save_local(str(FAISS_INDEX_DIRECTORY))
    return faiss_store


def query_smart_inventory_rag(user_query: str, faiss_store: Any, groq_api_key: str) -> str:
    """Retrieve inventory context and return a practical Groq-generated recommendation."""
    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError("user_query must be a non-empty question.")
    if faiss_store is None or not hasattr(faiss_store, "similarity_search"):
        raise TypeError("faiss_store must be a LangChain FAISS vector store.")
    if not isinstance(groq_api_key, str) or not groq_api_key.strip():
        raise ValueError("A Groq API key is required to generate inventory advice.")

    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise ImportError("Install langchain-groq to query the inventory assistant.") from exc

    try:
        documents = faiss_store.similarity_search(user_query, k=5)
    except Exception as exc:
        raise RuntimeError(f"Could not retrieve inventory context: {exc}") from exc
    if not documents:
        return "No matching inventory records were found. Refresh the inventory knowledge base and try again."

    context = "\n\n".join(document.page_content for document in documents)
    prompt = f"""You are SmartStock AI, an operations assistant for an e-commerce store manager.
Use only the inventory snapshot below. Give a concise, actionable answer. For stockout or
purchase-order questions, name products, cite the relevant quantities, and prioritize urgency.
If the snapshot lacks information needed to answer, say so plainly; never invent product data.

INVENTORY SNAPSHOT:
{context}

STORE MANAGER QUESTION: {user_query}
"""
    try:
        llm = ChatGroq(model=GROQ_MODEL, temperature=0, api_key=groq_api_key)
        response = llm.invoke(prompt)
        return str(response.content)
    except Exception as exc:
        raise RuntimeError(f"Groq could not generate inventory advice: {exc}") from exc


def _combine_inventory_data(sales_summary_df: pd.DataFrame, stock_df: pd.DataFrame) -> pd.DataFrame:
    """Merge user exports and establish a stable product-level RAG schema."""
    for frame_name, frame in (("sales_summary_df", sales_summary_df), ("stock_df", stock_df)):
        if "product_id" not in frame.columns:
            raise ValueError(f"{frame_name} must contain a 'product_id' column.")

    sales = sales_summary_df.copy()
    stock = stock_df.copy()
    combined = sales.merge(stock, on="product_id", how="outer", suffixes=("_sales", "_stock"))
    for field, default in {"product_name": "Unknown Product", "category": "Uncategorized"}.items():
        combined[field] = _coalesce_columns(combined, field, default).fillna(default)
    combined["predicted_units_next_week"] = pd.to_numeric(
        _coalesce_columns(combined, "predicted_units_next_week", 0), errors="coerce"
    ).fillna(0)
    combined["recent_units_sold"] = pd.to_numeric(
        _coalesce_columns(combined, "units_sold", 0), errors="coerce"
    ).fillna(0)
    combined["stock_on_hand"] = pd.to_numeric(
        _coalesce_columns(combined, "stock_on_hand", 0), errors="coerce"
    ).fillna(0)
    supplied_alert = _coalesce_columns(combined, "reorder_recommended", False)
    supplied_alert = supplied_alert.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})
    combined["reorder_recommended"] = supplied_alert | (
        combined["predicted_units_next_week"] > combined["stock_on_hand"]
    )
    return combined[[
        "product_id", "product_name", "category", "recent_units_sold",
        "predicted_units_next_week", "stock_on_hand", "reorder_recommended",
    ]]


def _coalesce_columns(frame: pd.DataFrame, base_name: str, default: Any) -> pd.Series:
    """Use an unsuffixed field first, then sales/stock variations from a merge."""
    candidates = [column for column in (base_name, f"{base_name}_sales", f"{base_name}_stock") if column in frame]
    if not candidates:
        return pd.Series(default, index=frame.index)
    result = frame[candidates[0]]
    for column in candidates[1:]:
        result = result.combine_first(frame[column])
    return result


def _format_product_document(row: pd.Series) -> str:
    """Create a compact, retrieval-friendly fact sheet for one product."""
    alert = "YES — replenish or review purchase order" if row["reorder_recommended"] else "No"
    shortfall = max(0, row["predicted_units_next_week"] - row["stock_on_hand"])
    return (
        f"Product ID: {row['product_id']}\n"
        f"Product: {row['product_name']}\n"
        f"Category: {row['category']}\n"
        f"Reported sales metric: {row['recent_units_sold']:.0f} units\n"
        f"Predicted demand next week: {row['predicted_units_next_week']:.0f} units\n"
        f"Current stock on hand: {row['stock_on_hand']:.0f} units\n"
        f"Estimated shortfall: {shortfall:.0f} units\n"
        f"Reorder recommended: {alert}"
    )


def _validate_dataframe(value: Any, name: str) -> None:
    if not isinstance(value, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame.")


class InventoryAssistant:
    """Graceful UI placeholder until a knowledge base and Groq key are supplied."""

    def answer(self, question: str) -> str:
        return "Build the inventory knowledge base, then ask: " + question
