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
import uuid
import shutil
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

# Add the personal-finance directory to the path to allow imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from ingest.csv_to_ledger import CSVToLedgerConverter
from analytics.analytics import AnalyticsEngine
from forms.fill_pdf import PDFFiller
from storage.duck import DuckDBManager

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
# Get the database path from the DuckDBManager
db_path = getattr(db_manager, 'db_path', '/Users/mmultra21/Documents/retro21_finance/data/finance.db')
analytics = AnalyticsEngine(db_path)
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

class DocumentAskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None

# Ensure documents directory exists
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

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

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), category: str = "general"):
    """
    Upload a document for processing and Q&A.
    """
    try:
        # Validate file type
        allowed_types = {'.pdf', '.txt', '.png', '.jpg', '.jpeg'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_types)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = DOCUMENTS_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the document
        try:
            from documents.document_processor import DocumentProcessor
            
            doc_processor = DocumentProcessor()
            
            # Extract text and create embeddings
            if file_ext == '.pdf':
                text_content, page_count = doc_processor.extract_text_from_pdf(str(file_path))
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                page_count = 1
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                text_content = doc_processor.extract_text_from_image(str(file_path))
                page_count = 1
            else:
                text_content = ""
                page_count = 1
            
            if text_content.strip():
                # Process and store the document
                chunks = doc_processor.process_document(
                    document_id=file_id,
                    content=text_content,
                    metadata={
                        "filename": file.filename,
                        "category": category,
                        "file_type": file_ext,
                        "upload_date": datetime.now().isoformat()
                    }
                )
                
                chunk_count = len(chunks) if chunks else 0
                status = "processed"
                message = "Document uploaded and processed successfully"
                
            else:
                chunk_count = 0
                status = "failed"
                message = "Could not extract text from document"
            
        except ImportError:
            # Fallback if document processor isn't available
            page_count = 1
            chunk_count = 1
            status = "uploaded"
            message = "Document uploaded (basic processing only - full text extraction not available)"
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            page_count = 1
            chunk_count = 0
            status = "failed"
            message = f"Document uploaded but processing failed: {str(e)}"
        
        return {
            "success": True,
            "document_id": file_id,
            "filename": file.filename,
            "page_count": page_count,
            "chunks": chunk_count,
            "status": status,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/documents")
async def list_documents():
    """
    Get list of uploaded documents.
    """
    try:
        documents = []
        
        # In a real app, this would query a database
        # For now, scan the uploads directory
        if DOCUMENTS_DIR.exists():
            for file_path in DOCUMENTS_DIR.glob("*"):
                if file_path.is_file():
                    file_stats = file_path.stat()
                    file_id = file_path.stem
                    
                    # Mock document data
                    doc = {
                        "id": file_id,
                        "filename": f"Document_{file_id[:8]}{file_path.suffix}",
                        "category": "general",
                        "upload_date": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        "file_size": file_stats.st_size,
                        "page_count": 1,
                        "status": "processed"
                    }
                    documents.append(doc)
        
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    """
    try:
        # Find and delete the file
        deleted = False
        for file_path in DOCUMENTS_DIR.glob(f"{document_id}.*"):
            if file_path.is_file():
                file_path.unlink()
                deleted = True
                break
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/documents/ask")
async def ask_document_question(request: DocumentAskRequest):
    """
    Ask a question about uploaded documents using Hermes3 LLM.
    """
    try:
        # Import here to avoid circular imports
        from llm.hermes_client import HermesClient
        from documents.document_processor import DocumentProcessor
        
        # Initialize components
        hermes = HermesClient()
        doc_processor = DocumentProcessor()
        
        # Check if Hermes server is available
        if not hermes.health_check():
            return {
                "success": False,
                "answer": "🔴 Hermes3 LLM server is not responding. Please ensure it's running on http://127.0.0.1:11434\n\nTo start Hermes3:\n```bash\n./run_hermes3.sh\n```",
                "sources": [],
                "error": "LLM server unavailable"
            }
        
        # Search for relevant document chunks
        search_results = []
        try:
            if hasattr(doc_processor, 'search'):
                search_results = doc_processor.search(
                    query=request.question,
                    document_ids=request.document_ids,
                    n_results=3
                )
        except Exception as search_error:
            logger.warning(f"Document search failed: {search_error}")
        
        # If no relevant documents found
        if not search_results:
            no_docs_prompt = f"""You are a helpful financial assistant. The user asked: "{request.question}"

However, I couldn't find any uploaded documents that contain relevant information to answer this question.

Please provide a helpful response that:
1. Acknowledges that no relevant documents were found
2. Explains what types of documents would be needed to answer this question
3. Offers to provide general financial guidance on the topic if possible

Keep the response friendly and constructive."""

            llm_response = hermes.generate_completion(
                prompt=no_docs_prompt,
                max_tokens=300,
                temperature=0.6
            )
            
            if llm_response.success:
                answer = llm_response.text.strip()
            else:
                answer = "I couldn't find any relevant information in your uploaded documents to answer this question. Please upload relevant financial documents (PDFs, bank statements, tax forms, etc.) and try again."
            
            return {
                "success": True,
                "answer": answer,
                "sources": [],
                "question": request.question,
                "strategy": "no_documents"
            }
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            
            if text.strip():
                context_parts.append(f"[Document {i+1}]: {text.strip()}")
                
                sources.append({
                    "document_id": metadata.get('document_id', ''),
                    "chunk_index": metadata.get('chunk_index', 0),
                    "relevance_score": score,
                    "text_preview": text[:100] + "..." if len(text) > 100 else text
                })
        
        # Create the Q&A prompt
        context = "\n\n".join(context_parts)
        qa_prompt = f"""You are a helpful financial document assistant. You have been provided with relevant excerpts from the user's financial documents to answer their question.

QUESTION: {request.question}

RELEVANT DOCUMENT EXCERPTS:
{context}

Please provide a clear, accurate answer based on the document excerpts above. If the excerpts don't contain enough information to fully answer the question, say so clearly. Always cite which document(s) you're referencing in your answer.

Focus on being helpful and accurate. Use a friendly, professional tone.

ANSWER:"""
        
        # Generate answer using Hermes3
        llm_response = hermes.generate_completion(
            prompt=qa_prompt,
            max_tokens=500,
            temperature=0.3,  # Lower temperature for more factual responses
            stop_sequences=["QUESTION:", "DOCUMENT EXCERPTS:", "---"]
        )
        
        if llm_response.success:
            return {
                "success": True,
                "answer": llm_response.text.strip(),
                "sources": sources,
                "question": request.question,
                "context_used": len(context_parts),
                "strategy": "document_qa",
                "llm_usage": llm_response.usage
            }
        else:
            return {
                "success": False,
                "answer": f"Error generating answer: {llm_response.error}",
                "sources": sources,
                "error": llm_response.error
            }
        
    except ImportError as e:
        logger.error(f"Missing dependencies for document Q&A: {e}")
        return {
            "success": False,
            "answer": "Document Q&A system not fully configured. Missing dependencies for document processing or LLM integration.",
            "sources": [],
            "error": f"Import error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing document question: {e}")
        return {
            "success": False,
            "answer": f"Sorry, I encountered an error while processing your question: {str(e)}",
            "sources": [],
            "error": str(e)
        }

@app.post("/narrate")
async def narrate(request: NarrateRequest):
    """
    Generate narrative text from structured facts using local LLM.
    Backend securely composes prompts and communicates with Hermes.
    """
    try:
        # Import here to avoid circular imports and handle missing dependencies gracefully
        from llm.hermes_client import HermesClient
        
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
        from llm.prompts import get_narrative_templates
        
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