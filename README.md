# Payout Process

A React TypeScript frontend with Python FastAPI backend that allows users to upload PDF files and extract JSON structure using OpenAI Vision API.

## Features

- Upload PDF files
- Display PDF in one frame
- Extract and display JSON structure in adjacent frame using OpenAI Vision API
- Built for Vercel deployment

## Project Structure

```
payout/
├── frontend/          # React TypeScript frontend
├── backend/           # Python FastAPI backend
└── README.md
```

## Setup

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

Create a `.env` file in the backend directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```