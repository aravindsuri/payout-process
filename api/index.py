import os
import base64
import io
import json
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2

app = FastAPI(title="Payout Process API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Payout Process API is running"}

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text.strip():
                text += f"--- Page {page_num + 1} ---\n{page_text}\n"
        
        print(f"Extracted {len(text)} characters from PDF")
        return text[:6000] if len(text) > 6000 else text  # Reasonable limit for OpenAI
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def convert_pdf_to_image(pdf_bytes: bytes) -> str:
    """Convert first page of PDF to base64 image for vision API."""
    try:
        import fitz  # PyMuPDF for image conversion
        doc = fitz.open("pdf", pdf_bytes)
        page = doc.load_page(0)
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_data).decode('utf-8')
    except ImportError:
        print("PyMuPDF not available - skipping image conversion")
        return ""
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
        return ""

@app.get("/api/test")
def test_simple():
    """Simple test endpoint."""
    return {"status": "working", "message": "API is responding"}

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """Simplified PDF analysis - just extract text for now."""
    try:
        print(f"Received file: {file.filename}")
        
        if not file.filename or not file.filename.endswith('.pdf'):
            return {
                "success": False,
                "error": "Only PDF files are supported"
            }
        
        # Read and extract text
        pdf_bytes = await file.read()
        print(f"PDF size: {len(pdf_bytes)} bytes")
        
        # Extract text using PyPDF2
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n"
            
            print(f"Extracted {len(text)} characters")
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "Could not extract text from PDF"
                }
            
            # For now, just return the extracted text
            # Later we can add OpenAI analysis
            return {
                "success": True,
                "data": {
                    "extracted_text": text,
                    "character_count": len(text),
                    "page_count": len(pdf_reader.pages),
                    "note": "Text extraction successful - OpenAI analysis temporarily disabled"
                }
            }
            
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return {
                "success": False,
                "error": f"PDF extraction failed: {str(e)}"
            }
            
    except Exception as e:
        print(f"General error: {e}")
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }

@app.post("/api/debug-extract")
async def debug_extract(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        pdf_bytes = await file.read()
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        return {
            "success": True,
            "data": {
                "extracted_text": pdf_text,
                "character_count": len(pdf_text),
                "note": "Raw text extraction for debugging"
            }
        }
        
    except Exception as e:
        print(f"Error in debug extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Error in debug extraction: {str(e)}")

# Vercel handler
handler = app