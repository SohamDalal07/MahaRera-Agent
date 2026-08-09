import sys
import re
sys.modules['regex'] = re

# Force UTF-8 stdout encoding for Windows console printing (e.g., EasyOCR download progress bars)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
Builds the legal knowledge base.

Run only when:
1. New legal PDFs are added.
2. You want to rebuild the FAISS index.
"""

from pathlib import Path

from project.ocr_loader import load_pdf_with_ocr
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# -----------------------------
# STEP 1 : Load every PDF
# -----------------------------

all_documents = []

pdf_files = Path("knowledge_base").rglob("*.pdf")

for pdf in pdf_files:

    print(f"Loading {pdf.name}")

    documents = load_pdf_with_ocr(str(pdf))

    # Add useful metadata
    for doc in documents:

        doc.metadata["document_name"] = pdf.stem

        doc.metadata["document_type"] = pdf.parent.name

    all_documents.extend(documents)

print(f"\nTotal Pages : {len(all_documents)}")


# -----------------------------
# STEP 2 : Split into chunks
# -----------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(all_documents)

print(f"Total Chunks : {len(chunks)}")


# -----------------------------
# STEP 3 : Embedding Model
# -----------------------------

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)


# -----------------------------
# STEP 4 : Build FAISS
# -----------------------------

vector_store = FAISS.from_documents(
    chunks,
    embedding_model
)


# -----------------------------
# STEP 5 : Save
# -----------------------------

vector_store.save_local("vector_store")

print("\nKnowledge Base Created Successfully!")