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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
        return ""

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        pdf_bytes = await file.read()
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        # Convert to image for vision analysis
        image_base64 = convert_pdf_to_image(pdf_bytes)
        
        # Prepare messages for OpenAI
        messages_content = []
        
        if image_base64:
            messages_content = [
                {
                    "type": "text",
                    "text": f"""You are an expert document analyst. Extract ALL information from this PDF document and return it as a comprehensive JSON structure.

EXTRACT EVERYTHING:
- Document type and title
- All dates (creation, due dates, effective dates, etc.)
- All parties involved (names, addresses, contact info)
- All monetary amounts and line items
- All reference numbers, IDs, contract numbers
- All signature fields and their status
- All terms, conditions, and important details

CRITICAL: Return ONLY valid JSON. No explanations or additional text.

PDF Text Content:
{pdf_text}

Return as complete JSON with all extracted data."""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}"
                    }
                }
            ]
        else:
            messages_content = f"""You are an expert document analyst. Extract ALL information from this PDF document and return it as a comprehensive JSON structure.

EXTRACT EVERYTHING:
- Document type and title  
- All dates (creation, due dates, effective dates, etc.)
- All parties involved (names, addresses, contact info)
- All monetary amounts and line items
- All reference numbers, IDs, contract numbers
- All signature fields and their status
- All terms, conditions, and important details

CRITICAL: Return ONLY valid JSON. No explanations or additional text.

PDF Text Content:
{pdf_text}

Return as complete JSON with all extracted data."""

        # Analyze with OpenAI API
        try:
            print("Making OpenAI API call...")
            model = "gpt-4o-mini" if image_base64 else "gpt-3.5-turbo"
            print(f"Using model: {model}")
            
            if image_base64:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": messages_content
                        }
                    ],
                    max_tokens=3000
                )
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user", 
                            "content": messages_content
                        }
                    ],
                    max_tokens=3000
                )
            
            print("OpenAI API call successful")
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

        # Process response
        content = response.choices[0].message.content
        print(f"Received {len(content)} characters from OpenAI")

        # Try to parse as JSON
        try:
            # Clean the content to extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]
                parsed_data = json.loads(json_content)
                
                return {
                    "success": True,
                    "data": parsed_data
                }
            else:
                # If no JSON structure found, return as structured text
                return {
                    "success": True,
                    "data": {
                        "document_analysis": content,
                        "extracted_text": pdf_text[:500],
                        "note": "AI analysis provided as text - JSON structure not detected"
                    }
                }
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "success": True,
                "data": {
                    "document_analysis": content,
                    "extracted_text": pdf_text[:500],
                    "note": "AI analysis provided - JSON parsing failed"
                }
            }
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)