from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io
import PyPDF2

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is working"}

@app.get("/api/test") 
def test():
    return {"status": "working", "message": "Test endpoint working"}

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    try:
        # Check file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            return {
                "success": False,
                "error": f"Invalid file type: {file.filename}",
                "error_code": "INVALID_FILE_TYPE"
            }
        
        # Read file
        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            return {
                "success": False,
                "error": "Empty file received",
                "error_code": "EMPTY_FILE"
            }
        
        # Extract text with PyPDF2
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n"
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "Could not extract text from PDF",
                    "error_code": "NO_TEXT_EXTRACTED"
                }
            
            return {
                "success": True,
                "data": {
                    "extracted_text": text[:1000] + "..." if len(text) > 1000 else text,
                    "character_count": len(text),
                    "page_count": len(pdf_reader.pages),
                    "file_size_bytes": len(pdf_bytes)
                }
            }
            
        except Exception as pdf_error:
            return {
                "success": False,
                "error": f"PDF processing error: {str(pdf_error)}",
                "error_code": "PDF_PROCESSING_ERROR"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "GENERAL_ERROR"
        }

# Vercel handler
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)