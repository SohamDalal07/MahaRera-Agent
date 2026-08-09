import os
import hashlib
import numpy as np
from PIL import Image
import io
import fitz  # PyMuPDF
from langchain_core.documents import Document

# Lazy load EasyOCR reader
_reader = None

def get_easyocr_reader(langs=['en', 'mr']):
    global _reader
    if _reader is None:
        import easyocr
        print(f"Initializing EasyOCR Reader for languages: {langs}...")
        _reader = easyocr.Reader(langs)
    return _reader

def get_ocr_cache_path(pdf_path: str, page_idx: int) -> str:
    cache_dir = os.path.join("uploads", "ocr_cache")
    os.makedirs(cache_dir, exist_ok=True)
    path_hash = hashlib.md5(pdf_path.encode('utf-8')).hexdigest()[:8]
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return os.path.join(cache_dir, f"{base_name}_{path_hash}_page_{page_idx}.txt")

def is_legacy_corrupted(text: str) -> bool:
    """
    Detects if standard extraction text contains legacy Shivaji/KrutiDev Marathi font character corruption.
    """
    if not text:
        return False
    text_len = len(text)
    if text_len == 0:
        return False
        
    # Count characters in the extended ASCII range (128-255)
    legacy_count = sum(1 for c in text if 128 <= ord(c) <= 255)
    # Count specific characters commonly used by Shivaji legacy font signature
    signature_count = sum(text.count(c) for c in "Éú½þ¹õ¶Ê±èò")
    
    legacy_ratio = legacy_count / text_len
    signature_ratio = signature_count / text_len
    
    return (legacy_count > 40 and legacy_ratio > 0.02) or (signature_count > 20 and signature_ratio > 0.01)

def load_pdf_with_ocr(pdf_path: str) -> list[Document]:
    """
    Load PDF pages. If a page contains legacy font character corruption, perform OCR (with local caching).
    Otherwise, extract clean standard text directly (extremely fast).
    """
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    documents = []
    
    for page_idx in range(num_pages):
        page = doc.load_page(page_idx)
        standard_text = page.get_text("text")
        
        # Check if the page suffers from character corruption
        if is_legacy_corrupted(standard_text):
            cache_file = get_ocr_cache_path(pdf_path, page_idx)
            page_text = None
            
            # Check cache first
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        page_text = f.read()
                    print(f"Loaded cached OCR text for {os.path.basename(pdf_path)} - page {page_idx + 1}/{num_pages}")
                except Exception:
                    page_text = None
            
            if page_text is None:
                # Render page to image for OCR (zoom = 1.2 is optimized for speed on CPU)
                zoom = 1.2  
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                img_np = np.array(img)
                
                print(f"Running EasyOCR on {os.path.basename(pdf_path)} - page {page_idx + 1}/{num_pages} (This may take a moment)...")
                reader = get_easyocr_reader()
                ocr_results = reader.readtext(img_np, detail=0)
                page_text = "\n".join(ocr_results)
                
                # Save to cache
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(page_text)
                except Exception as e:
                    print(f"Failed to cache OCR text: {str(e)}")
        else:
            # Clean standard text (runs in milliseconds!)
            page_text = standard_text
            
        metadata = {
            "source": pdf_path,
            "page": page_idx + 1
        }
        documents.append(Document(page_content=page_text, metadata=metadata))
        
    return documents
