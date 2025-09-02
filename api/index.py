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
    """Simple PDF text extraction with detailed error reporting."""
    try:
        print(f"Received file: {getattr(file, 'filename', 'No filename')}")
        print(f"Content type: {getattr(file, 'content_type', 'No content type')}")
        
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            error_msg = f"Invalid file type. Received: {file.filename}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_code": "INVALID_FILE_TYPE"
            }
        
        print("Reading file bytes...")
        pdf_bytes = await file.read()
        print(f"File size: {len(pdf_bytes)} bytes")
        
        if len(pdf_bytes) == 0:
            return {
                "success": False,
                "error": "Empty file received",
                "error_code": "EMPTY_FILE"
            }
        
        print("Creating PyPDF2 reader...")
        # Extract text using PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        print(f"PDF has {len(pdf_reader.pages)} pages")
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n"
                print(f"Page {page_num + 1}: extracted {len(page_text) if page_text else 0} characters")
            except Exception as page_error:
                print(f"Error extracting page {page_num + 1}: {page_error}")
                continue
        
        print(f"Total extracted text: {len(text)} characters")
        
        if not text.strip():
            return {
                "success": False,
                "error": "Could not extract any readable text from PDF",
                "error_code": "NO_TEXT_EXTRACTED",
                "debug_info": {
                    "page_count": len(pdf_reader.pages),
                    "file_size": len(pdf_bytes)
                }
            }
        
        print("Successfully extracted text, returning response")
        return {
            "success": True,
            "data": {
                "extracted_text": text[:1000] + "..." if len(text) > 1000 else text,  # Truncate for response
                "character_count": len(text),
                "page_count": len(pdf_reader.pages),
                "file_size": len(pdf_bytes)
            }
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg,
            "error_code": "GENERAL_ERROR",
            "error_type": type(e).__name__
        }

# Vercel handler
handler = app