import sys
import re
sys.modules['regex'] = re

import os
import hashlib
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor

from langchain_community.document_loaders import PyPDFLoader
from project.analyze import (
    load_vector_store,
    build_retriever,
    build_llm,
    analyze_clause,
    build_context,
    invoke_llm_with_retry,
)
from project.utils import extract_clauses
from project.prompts import BATCH_PROMPT_TEMPLATE
from project.parser import parse_batch_response

app = FastAPI(title="MahaRERA Compliance Auditor API")

# Add CORS Middleware to connect with React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

class AnalyzeRequest(BaseModel):
    clauses: list[str]

@app.post("/api/extract")
async def extract_agreement_clauses(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join("uploads", "agreement.pdf")
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        agreement_text = "\n".join(page.page_content for page in pages)
        clauses = extract_clauses(agreement_text)
        return {"clauses": clauses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract clauses: {str(e)}")

def perform_batch_analysis(clauses: list[str], retriever, llm) -> list[dict]:
    results = []
    batch_size = 5
    batches = [clauses[i:i + batch_size] for i in range(0, len(clauses), batch_size)]
    
    for batch_idx, batch in enumerate(batches):
        batch_data = []
        for idx, clause in enumerate(batch):
            global_idx = batch_idx * batch_size + idx
            legal_docs = retriever.invoke(clause)
            from project.retriever import filter_docs
            filtered_docs = filter_docs(legal_docs)
            context = build_context(filtered_docs[:5])
            
            batch_data.append({
                "index": global_idx + 1,
                "clause": clause,
                "context": context,
                "filtered_docs": filtered_docs
            })
            
        # Format the batch prompt
        prompt_lines = []
        for item in batch_data:
            prompt_lines.append(f"Clause Index: {item['index']}")
            prompt_lines.append(f"Agreement Clause Text:\n{item['clause']}")
            prompt_lines.append(f"Retrieved Legal Context:\n{item['context']}")
            prompt_lines.append("-" * 40)
            
        prompt_content = "\n".join(prompt_lines)
        prompt = BATCH_PROMPT_TEMPLATE.format(clauses_with_context=prompt_content)
        
        # Invoke model with retry
        response = invoke_llm_with_retry(llm, prompt)
        
        # Parse the batch response
        batch_results = parse_batch_response(response.content if hasattr(response, 'content') else str(response))
        
        # Map responses back to results
        for item in batch_data:
            audit_res = None
            for r in batch_results:
                if r.get("index") == item["index"]:
                    audit_res = r
                    break
            
            if not audit_res and batch_results:
                idx_in_batch = item["index"] - (batch_idx * batch_size + 1)
                if idx_in_batch < len(batch_results):
                    audit_res = batch_results[idx_in_batch]
                    
            if not audit_res:
                audit_res = {
                    "status": "Needs Review",
                    "confidence": 0,
                    "reason": "Failed to parse model response for this clause.",
                    "citations": [],
                    "recommendation": ""
                }
                
            # Normalize and ensure values
            audit_res["clause"] = item["clause"]
            audit_res["index"] = item["index"]
            
            # Format retrieved context for frontend
            audit_res["retrieved_context"] = [
                {
                    "document": doc.metadata.get("document_name"),
                    "page": doc.metadata.get("page"),
                    "section": doc.metadata.get("document_type"),
                    "content": doc.page_content,
                }
                for doc in item["filtered_docs"][:5]
            ]
            
            # Fallback citations if empty
            if not audit_res.get("citations"):
                audit_res["citations"] = [
                    {
                        "document": doc.metadata.get("document_name"),
                        "page": doc.metadata.get("page"),
                        "section": doc.metadata.get("document_type"),
                    }
                    for doc in item["filtered_docs"][:3]
                ]
                
            results.append(audit_res)
            
    return results

@app.post("/api/analyze")
async def analyze_selected_clauses(payload: AnalyzeRequest):
    if not payload.clauses:
        raise HTTPException(status_code=400, detail="No clauses provided for analysis.")
        
    try:
        db = load_vector_store()
        retriever = build_retriever(db)
        llm = build_llm()
        
        results = perform_batch_analysis(payload.clauses, retriever, llm)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-pdf")
async def analyze_pdf_agreement(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    os.makedirs("uploads", exist_ok=True)
    try:
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file contents: {str(e)}")
        
    # Check JSON Cache
    cache_path = os.path.join("uploads", "audit_cache.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
            
    if file_hash in cache:
        print(f"Cache hit for hash: {file_hash}. Returning cached results.")
        return {"results": cache[file_hash]}
        
    file_path = os.path.join("uploads", "agreement.pdf")
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    try:
        # 1. Parse PDF and extract clauses
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        agreement_text = "\n".join(page.page_content for page in pages)
        clauses = extract_clauses(agreement_text)
        
        if not clauses:
            return {"results": []}
            
        # Limit to the top 20 clauses to ensure reasonable response times (matches original project)
        selected_clauses = clauses[:20]
        
        db = load_vector_store()
        retriever = build_retriever(db)
        llm = build_llm()
        
        results = perform_batch_analysis(selected_clauses, retriever, llm)
        
        # Save to JSON Cache
        cache[file_hash] = results
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)

