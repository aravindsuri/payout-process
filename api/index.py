import os
import base64
import io
import json
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Payout Process API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

@app.get("/api/test-env")
def test_environment():
    """Test endpoint to check environment variables and basic functionality."""
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "status": "ok",
        "openai_api_key_set": bool(api_key),
        "openai_api_key_length": len(api_key) if api_key else 0,
        "openai_api_key_prefix": api_key[:10] + "..." if api_key and len(api_key) > 10 else "None",
        "env_vars": list(os.environ.keys())[:10],  # First 10 env vars for debugging
        "available_modules": {
            "PyPDF2": True,
            "fitz": True,
            "openai": True
        }
    }

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    try:
        # Detailed logging for debugging
        print(f"Received file: {file.filename}")
        
        if not file.filename.endswith('.pdf'):
            return {
                "success": False,
                "error": "Only PDF files are supported",
                "error_type": "invalid_file_type"
            }
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured",
                "error_type": "missing_api_key"
            }
        
        pdf_bytes = await file.read()
        print(f"PDF file size: {len(pdf_bytes)} bytes")
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_bytes)
        print(f"Extracted text length: {len(pdf_text)} characters")
        
        if not pdf_text.strip():
            return {
                "success": False,
                "error": "Could not extract text from PDF",
                "error_type": "pdf_extraction_failed"
            }
        
        # Convert to image for vision analysis
        image_base64 = convert_pdf_to_image(pdf_bytes)
        has_image = bool(image_base64)
        print(f"Image conversion successful: {has_image}")
        
        # Simple analysis first (text-only)
        try:
            print("Making OpenAI API call...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user", 
                        "content": f"""Extract key information from this document and return it as JSON:

PDF Text:
{pdf_text[:2000]}

Return a JSON object with fields like: document_type, amounts, dates, parties, etc."""
                    }
                ],
                max_tokens=1500
            )
            
            print("OpenAI API call successful")
            content = response.choices[0].message.content
            print(f"Received response: {len(content)} characters")
            
            # Try to parse as JSON
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    parsed_data = json.loads(json_content)
                    
                    return {
                        "success": True,
                        "data": parsed_data,
                        "metadata": {
                            "text_length": len(pdf_text),
                            "has_image": has_image,
                            "model_used": "gpt-3.5-turbo"
                        }
                    }
                else:
                    return {
                        "success": True,
                        "data": {
                            "raw_analysis": content,
                            "extracted_text": pdf_text[:500]
                        },
                        "metadata": {
                            "note": "JSON parsing failed, returning raw analysis"
                        }
                    }
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return {
                    "success": True,
                    "data": {
                        "raw_analysis": content,
                        "extracted_text": pdf_text[:500]
                    },
                    "metadata": {
                        "note": f"JSON parsing failed: {str(e)}"
                    }
                }
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "error_type": "openai_api_error",
                "extracted_text": pdf_text[:500]
            }
            
    except Exception as e:
        print(f"General error: {e}")
        return {
            "success": False,
            "error": f"Error processing PDF: {str(e)}",
            "error_type": "general_error"
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