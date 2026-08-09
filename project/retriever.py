from typing import Iterable

from langchain_community.vectorstores import FAISS


def build_retriever(db: FAISS):
    return db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 8,
            "fetch_k": 20,
            "lambda_mult": 0.5,
        },
    )


def filter_docs(docs: Iterable) -> list:
    filtered = []
    for doc in docs:
        doc_type = (doc.metadata or {}).get("document_type", "").lower()
        if doc_type in {"acts", "rules", "regulations"}:
            filtered.append(doc)
    if filtered:
        return filtered
    return list(docs)
