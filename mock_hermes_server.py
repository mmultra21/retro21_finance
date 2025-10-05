#!/usr/bin/env python3
"""
Mock Hermes LLM Server for Testing
Simulates the llama.cpp server API for testing purposes
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock Hermes LLM Server", version="1.0.0-test")

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 150
    temperature: float = 0.3
    stop: Optional[List[str]] = None
    stream: bool = False

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "server": "Mock Hermes LLM Server",
        "model": "mock-hermes-3-llama-3.1",
        "version": "1.0.0-test",
        "status": "operational",
        "endpoints": {
            "health": "GET /health - Health check",
            "completion": "POST /completion - Text completion"
        },
        "note": "This is a mock server for testing. Replace with real Hermes/llama.cpp in production."
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model": "mock-hermes"}

@app.post("/completion")
async def completion(request: CompletionRequest):
    """
    Mock completion endpoint.
    Generates contextual responses based on the prompt content.
    """
    prompt = request.prompt.lower()

    # Generate contextual responses based on prompt keywords
    if "monthly" in prompt or "summary" in prompt:
        response_text = (
            "In January 2024, you earned $5,250 and spent $3,847.62, "
            "resulting in net savings of $1,402.38 (26.7% savings rate). "
            "Your largest expense was housing at $2,100, followed by food and dining at $625."
        )
    elif "spending" in prompt or "pattern" in prompt:
        response_text = (
            "Your food and dining expenses totaled $625 across 23 transactions, "
            "averaging $27.17 per transaction. The 15.7% increase from last month "
            "suggests you may want to review your restaurant spending habits."
        )
    elif "budget" in prompt or "goal" in prompt:
        response_text = (
            "You're making excellent progress toward your $15,000 vacation savings goal! "
            "At $8,250 saved (55% complete) with consistent $1,650 monthly contributions, "
            "you're on track to reach your December 2024 target."
        )
    elif "categor" in prompt:
        # Transaction categorization
        if "grocery" in prompt or "food" in prompt:
            response_text = "Food & Groceries"
        elif "gas" in prompt or "fuel" in prompt:
            response_text = "Transportation"
        elif "electric" in prompt or "utility" in prompt:
            response_text = "Utilities"
        elif "coffee" in prompt or "starbucks" in prompt:
            response_text = "Dining & Beverages"
        else:
            response_text = "General Expenses"
    else:
        # Generic financial insight
        response_text = (
            "Based on the financial data provided, you're maintaining healthy "
            "financial habits with a positive savings rate and controlled spending."
        )

    return {
        "content": response_text,
        "model": "mock-hermes-3-llama-3.1",
        "usage": {
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(request.prompt.split()) + len(response_text.split())
        },
        "stop_reason": "stop"
    }

if __name__ == "__main__":
    print("🤖 Starting Mock Hermes LLM Server on http://127.0.0.1:11434")
    print("📝 This simulates a llama.cpp server for testing purposes")
    uvicorn.run(app, host="127.0.0.1", port=11434, log_level="info")
