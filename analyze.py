import sys
import re
sys.modules['regex'] = re

"""
analyze.py


Purpose:
---------
This file analyzes a Builder-Buyer Agreement against the
MahaRERA legal knowledge base.

Pipeline:

Agreement PDF
      ↓
Split into chunks
      ↓
Retrieve relevant legal sections
      ↓
Ask Qwen to compare
      ↓
Generate compliance report
"""

# -------------------------------
# Imports
# -------------------------------

from langchain_community.document_loaders import PyPDFLoader

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

from langchain_ollama import ChatOllama


# -------------------------------
# STEP 1
# Load Embedding Model
# -------------------------------

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)


# -------------------------------
# STEP 2
# Load FAISS Vector Store
# -------------------------------

db = FAISS.load_local(
    "vector_store",
    embedding_model,
    allow_dangerous_deserialization=True
)


# -------------------------------
# STEP 3
# Load Local LLM (Qwen)
# -------------------------------

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)


# -------------------------------
# STEP 4
# Load Builder Agreement
# -------------------------------

loader = PyPDFLoader(
    "uploads/agreement.pdf"
)

documents = loader.load()


# -------------------------------
# STEP 5
# Extract Agreement Clauses
# -------------------------------

import re

# Merge all pages into one string
agreement_text = ""

for page in documents:
    agreement_text += page.page_content + "\n"

# This regex captures clauses like:
# 1.1
# 2.5
# 15.10
# 20.1
pattern = re.compile(r'(?m)(^\d+(?:\.\d+)+\b.*?)(?=^\d+(?:\.\d+)+\b|\Z)', re.DOTALL)


def is_definition_clause(text):
    return bool(re.search(
        r'\bshall\s+(?:mean|have the meaning|include|refer to|constitute)\b|\bmeans\b',
        text,
        flags=re.IGNORECASE,
    ))


def is_table_clause(text):
    text = text.strip()
    if len(text) < 120 and re.search(r'\b\d+\s+BHK\b', text, flags=re.IGNORECASE):
        return True
    if len(text) < 100 and re.search(r'^\s*\d+\s+\S+', text, flags=re.MULTILINE):
        return True
    if re.search(r'(^|\n)(Annexure|Schedule|Appendix|Table|Sr\.\s*No\.|Particulars|Common Areas)', text, flags=re.IGNORECASE):
        return True
    return False


def is_valid_clause(text):
    if is_definition_clause(text):
        return True
    if is_table_clause(text):
        return False
    if len(text.split()) < 20:
        return False
    if re.search(r'\b(shall|must|may|liable|obliged|agreement|promoter|allottee|possession|maintenance|notice|payment|registration|completion|occupancy|development)\b', text, flags=re.IGNORECASE):
        return True
    return len(text) > 160


matches = [m.group(1).strip() for m in pattern.finditer(agreement_text)]
clauses = [m for m in matches if m and m.strip() and is_valid_clause(m)]

if len(clauses) == 0:
    print("=" * 80)
    print(agreement_text[:5000])
    print("=" * 80)

print(f"\nTotal Clauses Found : {len(clauses)}\n")


# -------------------------------
# STEP 6
# Analyze Each Chunk
# -------------------------------

for i, clause in enumerate(clauses[:5]):

    print("=" * 100)
    print(f"CLAUSE {i+1}")
    print("=" * 100)

    print("\nAgreement Clause:\n")
    print(clause[:500])      # Show first 500 chars

    print("\nSearching legal knowledge base...\n")

    legal_docs = []
    scores = []

    if hasattr(db, 'similarity_search_with_score'):
        results = db.similarity_search_with_score(clause, k=8)
        legal_docs = [doc for doc, score in results]
        scores = [score for doc, score in results]
    else:
        legal_docs = db.similarity_search(clause, k=8)

    legal_docs = legal_docs[:3]

    context = ""

    print("\nRetrieved Legal References\n")

    for idx, doc in enumerate(legal_docs, start=1):

        print("----------------------------------")

        print("Result #:", idx)
        print("Document :", doc.metadata.get("document_name"))
        print("Type     :", doc.metadata.get("document_type"))
        print("Page     :", doc.metadata.get("page"))
        if scores:
            print("Score    :", scores[idx-1])
        print()

        print(doc.page_content[:400])

        print()

        context += f"""
Document: {doc.metadata.get('document_name')}
Type: {doc.metadata.get('document_type')}
Page: {doc.metadata.get('page')}

{doc.page_content}

"""

    prompt = f"""
You are an expert MahaRERA Legal Compliance Officer.

Your task is to compare ONE Builder Agreement clause with the relevant MahaRERA laws.

Use ONLY the provided retrieved legal context. Do not invent or infer facts that are not explicitly supported by the context.

If the retrieved context is insufficient, unrelated, or clearly not about the clause, answer:

Status:
Needs Review

Reason:
Insufficient relevant legal context retrieved.

Relevant Law:

Recommendation:

If you answer Compliant or Non-Compliant, cite at least one exact document source from the provided context, including document name, type, and page.

Agreement Clause:

{clause}

-----------------------------------------

Retrieved Legal Context:

{context}

-----------------------------------------

Return ONLY in this format.

Status:
(Compliant / Non-Compliant / Needs Review)

Reason:

Relevant Law:

Recommendation:
"""

    response = llm.invoke(prompt)

    print("\nAI ANALYSIS\n")

    print(response.content)

    print("\n\n")