from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io
import os
import json
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    api_key = os.getenv("OPENAI_API_KEY")
    return {
        "status": "working", 
        "message": "Test endpoint working",
        "openai_configured": bool(api_key),
        "openai_key_length": len(api_key) if api_key else 0
    }

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
            
            # Now analyze with OpenAI for comprehensive field extraction
            try:
                print("Making OpenAI API call for comprehensive analysis...")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": f"""You are an expert document analyst. Analyze this document and extract ALL information in a comprehensive JSON structure.

EXTRACT EVERYTHING INCLUDING:
- Document type and title
- All dates (creation dates, due dates, effective dates, contract dates, etc.)
- All parties involved (names, companies, addresses, contact information, signatures)
- All monetary amounts, costs, fees, totals (with currency if specified)
- All reference numbers, IDs, invoice numbers, contract numbers, account numbers
- All line items, products, services described
- All terms, conditions, clauses, requirements
- Any tax information, payment terms, delivery details
- All other structured data fields present

IMPORTANT: Return ONLY valid JSON. No explanations or additional text.

Document Text:
{text}

Return as comprehensive JSON with nested objects for different sections."""
                        }
                    ],
                    max_tokens=3000,
                    temperature=0.1
                )
                
                print("OpenAI API call successful")
                ai_content = response.choices[0].message.content
                
                # Try to parse the AI response as JSON
                try:
                    # Find JSON in the response
                    json_start = ai_content.find('{')
                    json_end = ai_content.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_content = ai_content[json_start:json_end]
                        structured_data = json.loads(json_content)
                        
                        return {
                            "success": True,
                            "data": {
                                "structured_data": structured_data,
                                "metadata": {
                                    "character_count": len(text),
                                    "page_count": len(pdf_reader.pages),
                                    "file_size_bytes": len(pdf_bytes),
                                    "extraction_method": "OpenAI GPT-3.5-turbo",
                                    "raw_text_preview": text[:500] + "..." if len(text) > 500 else text
                                }
                            }
                        }
                    else:
                        # If JSON parsing fails, return the AI analysis as text
                        return {
                            "success": True,
                            "data": {
                                "ai_analysis": ai_content,
                                "metadata": {
                                    "character_count": len(text),
                                    "page_count": len(pdf_reader.pages),
                                    "file_size_bytes": len(pdf_bytes),
                                    "extraction_method": "OpenAI GPT-3.5-turbo (text format)",
                                    "note": "AI analysis provided as text - JSON structure not detected"
                                }
                            }
                        }
                        
                except json.JSONDecodeError as json_error:
                    print(f"JSON parsing error: {json_error}")
                    return {
                        "success": True,
                        "data": {
                            "ai_analysis": ai_content,
                            "metadata": {
                                "character_count": len(text),
                                "page_count": len(pdf_reader.pages),
                                "file_size_bytes": len(pdf_bytes),
                                "extraction_method": "OpenAI GPT-3.5-turbo (text format)",
                                "note": f"JSON parsing failed: {str(json_error)}"
                            }
                        }
                    }
                    
            except Exception as openai_error:
                print(f"OpenAI API error: {openai_error}")
                # Fallback to basic text extraction if OpenAI fails
                return {
                    "success": True,
                    "data": {
                        "extracted_text": text[:1000] + "..." if len(text) > 1000 else text,
                        "character_count": len(text),
                        "page_count": len(pdf_reader.pages),
                        "file_size_bytes": len(pdf_bytes),
                        "note": f"OpenAI analysis failed: {str(openai_error)}. Showing basic text extraction.",
                        "openai_error": str(openai_error)
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

@app.post("/api/debug-extract")
async def debug_extract(file: UploadFile = File(...)):
    """Simple debug endpoint that returns raw extracted text."""
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            return {
                "success": False,
                "error": f"Invalid file type: {file.filename}"
            }
        
        pdf_bytes = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text += f"--- Page {page_num + 1} ---\n{page_text}\n"
        
        return {
            "success": True,
            "data": {
                "extracted_text": text,
                "character_count": len(text),
                "page_count": len(pdf_reader.pages),
                "note": "Raw text extraction for debugging"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Debug extraction failed: {str(e)}"
        }

# Vercel handler
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)