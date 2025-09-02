import os
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2

app = FastAPI(title="Payout Process API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Payout Process API is running"}

@app.get("/api/test")
def test_simple():
    return {"status": "working", "message": "API is responding"}

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """Simple PDF text extraction."""
    try:
        if not file.filename or not file.filename.endswith('.pdf'):
            return {
                "success": False,
                "error": "Only PDF files are supported"
            }
        
        pdf_bytes = await file.read()
        
        # Extract text using PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text.strip():
                text += f"--- Page {page_num + 1} ---\n{page_text}\n"
        
        if not text.strip():
            return {
                "success": False,
                "error": "Could not extract text from PDF"
            }
        
        return {
            "success": True,
            "data": {
                "extracted_text": text,
                "character_count": len(text),
                "page_count": len(pdf_reader.pages)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }

# Vercel handler
handler = app