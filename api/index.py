import os
import io
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import PyPDF2

app = FastAPI(title="Payout Process API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Additional OPTIONS handler for preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/")
def health_check():
    return JSONResponse(
        content={"status": "healthy", "message": "Payout Process API is running"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.get("/api/test")
def test_simple():
    return JSONResponse(
        content={"status": "working", "message": "API is responding"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """Simple PDF text extraction with detailed error reporting."""
    try:
        print(f"Received file: {getattr(file, 'filename', 'No filename')}")
        print(f"Content type: {getattr(file, 'content_type', 'No content type')}")
        
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            error_msg = f"Invalid file type. Received: {file.filename}"
            print(error_msg)
            return JSONResponse(
                content={
                    "success": False,
                    "error": error_msg,
                    "error_code": "INVALID_FILE_TYPE"
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        print("Reading file bytes...")
        pdf_bytes = await file.read()
        print(f"File size: {len(pdf_bytes)} bytes")
        
        if len(pdf_bytes) == 0:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Empty file received",
                    "error_code": "EMPTY_FILE"
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
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
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Could not extract any readable text from PDF",
                    "error_code": "NO_TEXT_EXTRACTED",
                    "debug_info": {
                        "page_count": len(pdf_reader.pages),
                        "file_size": len(pdf_bytes)
                    }
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        print("Successfully extracted text, returning response")
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "extracted_text": text[:1000] + "..." if len(text) > 1000 else text,  # Truncate for response
                    "character_count": len(text),
                    "page_count": len(pdf_reader.pages),
                    "file_size": len(pdf_bytes)
                }
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return JSONResponse(
            content={
                "success": False,
                "error": error_msg,
                "error_code": "GENERAL_ERROR",
                "error_type": type(e).__name__
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )

@app.post("/api/debug-extract")
async def debug_extract(file: UploadFile = File(...)):
    """Simple debug endpoint that just returns extracted text."""
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Invalid file type. Received: {file.filename}"
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        pdf_bytes = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text += f"--- Page {page_num + 1} ---\n{page_text}\n"
        
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "extracted_text": text,
                    "character_count": len(text),
                    "page_count": len(pdf_reader.pages),
                    "note": "Raw text extraction for debugging"
                }
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": f"Debug extraction failed: {str(e)}"
            },
            headers={"Access-Control-Allow-Origin": "*"}
        )

# Vercel handler
handler = app