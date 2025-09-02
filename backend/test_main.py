from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
def health_check():
    return {"status": "working", "message": "Minimal test API"}

@app.get("/test")
def test_endpoint():
    return {"test": "success"}

# Vercel handler
handler = app