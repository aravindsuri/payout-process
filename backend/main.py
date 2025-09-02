import os
import base64
import io
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pdf2image import convert_from_bytes
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
    """Extract text content from PDF for context."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text[:2000]  # Limit text for API call
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def pdf_to_image_base64(pdf_bytes: bytes, page_num: int = 0) -> str:
    """Convert PDF page to base64 encoded image."""
    try:
        images = convert_from_bytes(pdf_bytes, first_page=page_num + 1, last_page=page_num + 1)
        if images:
            img_buffer = io.BytesIO()
            images[0].save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return base64.b64encode(img_buffer.getvalue()).decode()
        return ""
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
        return ""

@app.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Analyze PDF using OpenAI Vision API and extract structured data."""
    
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        pdf_bytes = await file.read()
        
        # Extract text for context
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        # Convert first page to image
        image_base64 = pdf_to_image_base64(pdf_bytes, 0)
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="Could not convert PDF to image")
        
        # Analyze with OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Please analyze this PDF document and extract structured data in JSON format. 

This appears to be a payout/payment related document. Please extract relevant information such as:
- Document type and title
- Dates (transaction date, due date, etc.)
- Amounts (total, subtotal, fees, etc.)
- Parties involved (payer, payee, company names)
- Account information (account numbers, routing numbers - but mask sensitive info)
- Transaction details
- Any other structured data you can identify

Text content from PDF: {pdf_text[:1000]}

Return the data as a well-structured JSON object with appropriate keys and values. Be thorough but organize the data logically."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )
        
        # Try to parse the response as JSON
        content = response.choices[0].message.content
        
        # Clean up the response to extract JSON
        try:
            # Look for JSON in the response
            import json
            import re
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_json = json.loads(json_str)
                return {
                    "success": True,
                    "data": parsed_json,
                    "raw_response": content
                }
            else:
                # If no valid JSON found, return structured response
                return {
                    "success": True,
                    "data": {
                        "document_analysis": content,
                        "extracted_text": pdf_text[:500],
                        "note": "AI analysis provided as text - JSON structure not detected"
                    },
                    "raw_response": content
                }
                
        except json.JSONDecodeError:
            # Return analysis as text if JSON parsing fails
            return {
                "success": True,
                "data": {
                    "document_analysis": content,
                    "extracted_text": pdf_text[:500],
                    "note": "AI analysis provided - JSON parsing failed"
                },
                "raw_response": content
            }
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing PDF: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Payout Process API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)