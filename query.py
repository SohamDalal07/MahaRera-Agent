import sys
import re
sys.modules['regex'] = re

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
import time

# Load embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

# Load FAISS
db = FAISS.load_local(
    "vector_store",
    embedding_model,
    allow_dangerous_deserialization=True
)

# Load local LLM
llm = OllamaLLM(model="qwen2.5:7b")

# User question
question = input("Ask your question: ")

# Retrieve relevant chunks
docs = db.similarity_search(question, k=3)

print("\n========== Retrieved Chunks ==========\n")

for i, doc in enumerate(docs, start=1):
    print(f"Chunk {i} (Page {doc.metadata['page'] + 1})")
    print(doc.page_content)
    print("-" * 70)

# Convert chunks to text
context = "\n\n".join(doc.page_content for doc in docs)

# Create prompt
prompt = f"""
You are a helpful assistant.

Answer only from the context below.

Context:
{context}

Question:
{question}
"""

# Generate answer
start = time.time()
response = llm.invoke(prompt)
end = time.time()
print(f"Time taken: {end - start:.2f} seconds")
print(response)