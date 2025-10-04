"""
FastAPI application for personal finance management.
Provides endpoints for ingesting transactions, querying data, and filling forms.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime, date
import csv
import io
from pathlib import Path

logger = logging.getLogger(__name__)

from ..ingest.csv_to_ledger import CSVToLedgerConverter
from ..analytics.analytics import AnalyticsEngine
from ..forms.fill_pdf import PDFFiller
from ..storage.duck import DuckDBManager

app = FastAPI(
    title="Personal Finance API",
    description="API for managing personal finances with double-entry bookkeeping",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DuckDBManager()
analytics = AnalyticsEngine(db_manager)
csv_converter = CSVToLedgerConverter()
pdf_filler = PDFFiller()

class TransactionQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account: Optional[str] = None
    category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class FormFillRequest(BaseModel):
    form_type: str
    data: Dict[str, Any]
    template_path: Optional[str] = None

class NarrateRequest(BaseModel):
    template: str
    facts: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...), bank: str = "unknown"):
    """
    Ingest transactions from a CSV file.
    """
    try:
        content = await file.read()
        csv_text = content.decode('utf-8')
        
        # Convert CSV to Beancount entries
        entries = csv_converter.convert(csv_text, bank)
        
        # Store in DuckDB
        transactions = csv_converter.to_transactions(entries)
        db_manager.insert_transactions(transactions)
        
        return {
            "message": f"Successfully ingested {len(entries)} transactions",
            "transactions_count": len(entries),
            "bank": bank
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@app.post("/query/transactions")
async def query_transactions(query: TransactionQuery):
    """
    Query transactions with filters.
    """
    try:
        filters = {}
        if query.start_date:
            filters['start_date'] = query.start_date
        if query.end_date:
            filters['end_date'] = query.end_date
        if query.account:
            filters['account'] = query.account
        if query.category:
            filters['category'] = query.category
        if query.min_amount:
            filters['min_amount'] = query.min_amount
        if query.max_amount:
            filters['max_amount'] = query.max_amount
            
        transactions = analytics.query_transactions(filters)
        return {
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error querying transactions: {str(e)}")

@app.get("/analytics/summary")
async def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get financial summary for a date range.
    """
    try:
        filters = {}
        if start_date:
            filters['start_date'] = datetime.fromisoformat(start_date).date()
        if end_date:
            filters['end_date'] = datetime.fromisoformat(end_date).date()
            
        summary = analytics.get_summary(filters)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating summary: {str(e)}")

@app.get("/analytics/cash-flow")
async def get_cash_flow(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "monthly"
):
    """
    Get cash flow analysis.
    """
    try:
        filters = {}
        if start_date:
            filters['start_date'] = datetime.fromisoformat(start_date).date()
        if end_date:
            filters['end_date'] = datetime.fromisoformat(end_date).date()
            
        cash_flow = analytics.get_cash_flow(filters, granularity)
        return cash_flow
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating cash flow: {str(e)}")

@app.post("/forms/fill")
async def fill_form(request: FormFillRequest):
    """
    Fill a PDF form with provided data.
    """
    try:
        output_path = pdf_filler.fill_form(
            form_type=request.form_type,
            data=request.data,
            template_path=request.template_path
        )
        
        return {
            "message": "Form filled successfully",
            "output_path": output_path,
            "form_type": request.form_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error filling form: {str(e)}")

@app.get("/forms/available")
async def get_available_forms():
    """
    Get list of available form types.
    """
    try:
        forms = pdf_filler.get_available_forms()
        return {"forms": forms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting forms: {str(e)}")

@app.post("/narrate")
async def narrate(request: NarrateRequest):
    """
    Generate narrative text from structured facts using local LLM.
    Backend securely composes prompts and communicates with Hermes.
    """
    try:
        # Import here to avoid circular imports and handle missing dependencies gracefully
        from ..llm.hermes_client import HermesClient
        
        # Initialize Hermes client
        hermes = HermesClient()
        
        # Check if Hermes server is available
        if not hermes.health_check():
            raise HTTPException(
                status_code=503, 
                detail="LLM server is not available. Please ensure Hermes is running."
            )
        
        # Compose prompt server-side for security
        facts_text = "\n".join(f"{k}: {v}" for k, v in request.facts.items())
        prompt = request.template.replace("{facts}", facts_text)
        
        # Generate narrative using Hermes
        response = hermes.generate_completion(
            prompt=prompt,
            max_tokens=400,
            temperature=0.6,  # Slightly more creative for narratives
            stop_sequences=["\n\n", "###", "---"]
        )
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: {response.error}"
            )
        
        return {
            "text": response.text,
            "success": True,
            "usage": response.usage
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="LLM client not available. Please check dependencies."
        )
    except Exception as e:
        logger.error(f"Error in narrate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Narration failed: {str(e)}")

@app.get("/narrate/templates")
async def get_narrative_templates():
    """
    Get available narrative templates for different financial scenarios.
    """
    try:
        from ..llm.prompts import get_narrative_templates
        
        templates = get_narrative_templates()
        
        # Return template names and descriptions
        template_info = {}
        for name, template in templates.items():
            # Extract description from template (first few lines)
            lines = template.split('\n')
            description = lines[0] if lines else "Financial narrative template"
            template_info[name] = {
                "name": name,
                "description": description,
                "template": template
            }
        
        return {"templates": template_info}
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Template system not available."
        )
    except Exception as e:
        logger.error(f"Error getting narrative templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving templates: {str(e)}")

# Production: Mount static files for built frontend
# This should be done after all API routes are defined
frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    # Mount static files (CSS, JS, images, etc.)
    app.mount("/static", StaticFiles(directory=str(frontend_dist_path / "static")), name="static")
    
    # Mount the main frontend app (this should be last to catch all remaining routes)
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="frontend")
    
    print(f"✅ Production mode: Serving frontend from {frontend_dist_path}")
else:
    print(f"⚠️  Frontend dist not found at {frontend_dist_path}")
    print("   Running in API-only mode. For production, build the frontend first:")
    print("   cd frontend && npm run build")

if __name__ == "__main__":
    import uvicorn
    
    # Check if we're in development or production mode
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        # Production: serve on all interfaces
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    else:
        # Development: enable reload and serve on localhost
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True, log_level="debug")