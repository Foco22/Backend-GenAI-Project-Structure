from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import uvicorn
import os
import time
import json
from datetime import datetime
import logging

# Import your functions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # For Cloud Run, log to stdout/stderr
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Redmine Assistant API",
    description="API for Redmine project management assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# API routes
@app.get("/")
async def root():
    return {"message": "Redmine Assistant API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Chat request model
class ChatRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None

# Chat response model
class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Import here to avoid circular imports
        from src.llm.openai import OpenAI
        
        # Initialize OpenAI client
        openai_client = OpenAI()
        
        # Get response from OpenAI
        response = openai_client.get_assistant_response(request.query, request.conversation_history)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


# For Google Cloud Run, we need to use the PORT environment variable
port = int(os.environ.get("PORT", 8080))

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)  # Disable reload for production to avoid duplicate schedulers
