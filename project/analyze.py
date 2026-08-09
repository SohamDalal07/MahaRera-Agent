import sys
import re
sys.modules['regex'] = re

import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from project.llm import build_llm
from project.prompts import PROMPT_TEMPLATE
from project.parser import parse_response
from project.retriever import build_retriever, filter_docs
from project.utils import extract_clauses
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1.5, min=2, max=12),
    reraise=True
)
def invoke_llm_with_retry(llm, prompt):
    return llm.invoke(prompt)


def load_vector_store():
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5"
    )
    return FAISS.load_local(
        "vector_store",
        embedding_model,
        allow_dangerous_deserialization=True,
    )


def load_agreement(path: str):
    loader = PyPDFLoader(path)
    return loader.load()


def build_context(docs):
    return "\n\n".join(
        f"Document: {doc.metadata.get('document_name')}\n"
        f"Type: {doc.metadata.get('document_type')}\n"
        f"Page: {doc.metadata.get('page')}\n\n"
        f"{doc.page_content}"
        for doc in docs
    )


def analyze_clause(clause: str, retriever, llm):
    legal_docs = retriever.invoke(clause)
    legal_docs = filter_docs(legal_docs)
    context = build_context(legal_docs[:5])
    prompt = PROMPT_TEMPLATE.format(clause=clause, context=context)
    response = invoke_llm_with_retry(llm, prompt)
    result = parse_response(response.content if hasattr(response, 'content') else str(response))
    
    # If LLM did not return any citations, fall back to the top retrieved document metadata
    if not result.get("citations"):
        result["citations"] = [
            {
                "document": doc.metadata.get("document_name"),
                "page": doc.metadata.get("page"),
                "section": doc.metadata.get("document_type"),
            }
            for doc in legal_docs[:3]
        ]
    return result



def analyze_agreement(path: str):
    db = load_vector_store()
    retriever = build_retriever(db)
    llm = build_llm()
    pages = load_agreement(path)
    agreement_text = "\n".join(page.page_content for page in pages)
    clauses = extract_clauses(agreement_text)
    results = []
    for clause in clauses[:20]:
        result = analyze_clause(clause, retriever, llm)
        result["clause"] = clause
        results.append(result)
    return results


def render_markdown_report(results: list[dict]) -> str:
    compliant = sum(1 for r in results if r.get("status") == "Compliant")
    non_compliant = sum(1 for r in results if r.get("status") == "Non-Compliant")
    needs_review = sum(1 for r in results if r.get("status") == "Needs Review")

    lines = [
        "# MahaRERA Compliance Report",
        "",
        f"- ✅ {compliant} Clauses Compliant",
        f"- ❌ {non_compliant} Clauses Non-Compliant",
        f"- ⚠️ {needs_review} Clauses Need Review",
        "",
        "---",
        "",
    ]

    for idx, item in enumerate(results, start=1):
        lines.extend([
            f"## Clause {idx}",
            "",
            f"**Status:** {item.get('status', 'Unknown')}",
            f"**Confidence:** {item.get('confidence', 0)}%",
            "",
            f"**Clause:**",
            "",
            item.get("clause", ""),
            "",
            f"**Reason:**",
            "",
            item.get("reason", ""),
            "",
            f"**Recommendation:**",
            "",
            item.get("recommendation", ""),
            "",
            "### Citations",
            "",
        ])
        for cite in item.get("citations", []):
            lines.append(f"- {cite.get('document', 'Unknown')} (Page {cite.get('page', 'N/A')}, Section: {cite.get('section', '')})")
        lines.extend(["", "---", ""])

    return "\n".join(lines)


def save_report(results, path="report.json"):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)


def save_markdown_report(results, path="report.md"):
    report_text = render_markdown_report(results)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(report_text)
    return report_text


if __name__ == "__main__":
    report = analyze_agreement("uploads/agreement.pdf")
    save_report(report, "report.json")
    save_markdown_report(report, "report.md")
    print(f"Report saved: report.json and report.md")
