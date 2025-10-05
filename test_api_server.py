#!/usr/bin/env python3
"""
Simplified API server for testing - doesn't require DuckDB
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Personal Finance API (Test Mode)",
    description="Test API for personal finance management",
    version="1.0.0-test"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NarrateRequest(BaseModel):
    template: str
    facts: Dict[str, Any]

class TransactionUpdate(BaseModel):
    merchant: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None

class ChatRequest(BaseModel):
    question: str

class DocumentAskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None

@app.post("/chat/financial-advice")
async def financial_advice_chat(request: ChatRequest):
    """Free-form financial advice chat with content filtering."""
    try:
        hermes_url = os.getenv('HERMES_URL', 'http://127.0.0.1:11434')
        
        try:
            import requests
            health_response = requests.get(f"{hermes_url}/health", timeout=2)
            if health_response.status_code != 200:
                raise HTTPException(status_code=503, detail="AI advisor not available")
        except:
            raise HTTPException(status_code=503, detail="AI advisor not available")
        
        system_prompt = """You are a knowledgeable financial advisor AI providing advice on personal finance, budgeting, debt management, taxes, savings, and investments. Only answer financial questions. Be concise (2-4 sentences). Question: """
        
        full_prompt = system_prompt + request.question + "\n\nAnswer:"
        
        import requests
        payload = {
            "prompt": full_prompt,
            "max_tokens": 500,
            "temperature": 0.7,
            "stop": ["\n\nQuestion:", "###"],
            "stream": False
        }
        
        response = requests.post(f"{hermes_url}/completion", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {"answer": data.get('content', '').strip(), "success": True}
        else:
            raise HTTPException(status_code=500, detail="AI generation failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "test"
    }

@app.get("/llm/health")
async def llm_health_check():
    """Proxy health check for LLM server to avoid CORS issues."""
    try:
        import requests
        hermes_url = os.getenv('HERMES_URL', 'http://127.0.0.1:11434')
        response = requests.get(f"{hermes_url}/health", timeout=2)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "online",
                "model": data.get("model", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "offline",
                "error": "LLM server returned non-200 status",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/forms/available")
async def get_available_forms():
    """Get list of available form types."""
    return {
        "forms": ["IRS-433A", "Budget-Worksheet", "Expense-Report"]
    }

@app.get("/narrate/templates")
async def get_narrative_templates():
    """Get available narrative templates."""
    templates = {
        "monthly_summary": {
            "name": "monthly_summary",
            "description": "Generate a monthly financial summary",
            "template": "Based on your financial data for {month}, provide a summary."
        },
        "spending_insight": {
            "name": "spending_insight",
            "description": "Analyze spending patterns",
            "template": "Analyze spending in {category} for insights."
        },
        "budget_progress": {
            "name": "budget_progress",
            "description": "Track budget goal progress",
            "template": "Track progress toward {goal}."
        }
    }
    return {"templates": templates}

@app.post("/narrate")
async def narrate(request: NarrateRequest):
    """
    Generate narrative text from structured facts using local LLM.
    """
    try:
        # Check if Hermes is available
        hermes_url = os.getenv('HERMES_URL', 'http://127.0.0.1:11434')

        try:
            import requests
            health_response = requests.get(f"{hermes_url}/health", timeout=2)
            if health_response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail="LLM server is not available. Please ensure Hermes is running."
                )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="LLM server is not available. Please ensure Hermes is running on port 11434."
            )

        # Compose prompt server-side
        facts_text = "\n".join(f"{k}: {v}" for k, v in request.facts.items())
        prompt = request.template.replace("{facts}", facts_text)

        # Call Hermes
        import requests
        payload = {
            "prompt": prompt,
            "max_tokens": 400,
            "temperature": 0.6,
            "stop": ["\n\n", "###", "---"],
            "stream": False
        }

        response = requests.post(
            f"{hermes_url}/completion",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "text": data.get('content', '').strip(),
                "success": True,
                "usage": data.get('usage', {})
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: HTTP {response.status_code}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in narrate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Narration failed: {str(e)}")

@app.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...), bank: str = Form("unknown")):
    """
    Ingest transactions from a CSV file and store in DuckDB.
    """
    try:
        import sys
        import csv
        from io import StringIO
        from decimal import Decimal
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        # Read CSV content
        content = await file.read()
        csv_text = content.decode('utf-8')

        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_text))
        transactions = []

        for row in csv_reader:
            # Support multiple CSV formats
            # Format 1: Bank statement (Account Number, Post Date, Check, Description, Debit, Credit, Status, Balance, Classification)
            # Format 2: Simple (date, merchant, amount, category, description)

            # Determine amount from Debit/Credit or direct amount field
            debit = row.get('Debit', row.get('debit', ''))
            credit = row.get('Credit', row.get('credit', ''))

            amount = 0.0  # Default
            try:
                if debit and debit.strip() and debit.strip() not in ['', '-', 'N/A']:
                    amount = -abs(float(debit.replace('$', '').replace(',', '').strip()))
                elif credit and credit.strip() and credit.strip() not in ['', '-', 'N/A']:
                    amount = abs(float(credit.replace('$', '').replace(',', '').strip()))
                else:
                    raw_amount = row.get('amount', row.get('Amount', '0'))
                    if raw_amount and str(raw_amount).strip():
                        amount = float(str(raw_amount).replace('$', '').replace(',', '').strip())
            except (ValueError, AttributeError):
                amount = 0.0  # Default to 0 if parsing fails

            # Get date from Post Date or date field
            raw_date = row.get('Post Date', row.get('post date', row.get('date', row.get('Date', ''))))

            # Parse date - handle various formats
            date_str = datetime.now().strftime('%Y-%m-%d')  # Default to today
            if raw_date and raw_date.strip():
                try:
                    # Try common date formats
                    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            parsed_date = datetime.strptime(raw_date.strip(), fmt)
                            date_str = parsed_date.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass  # Use default date if parsing fails

            # Get description from Description field or merchant
            description = row.get('Description', row.get('description', row.get('merchant', row.get('Merchant', 'Unknown'))))

            # Get check number if available
            check_number = row.get('Check', row.get('check', row.get('Check Number', '')))

            # Get category/classification
            category = row.get('Classification', row.get('classification', row.get('category', row.get('Category', 'Uncategorized'))))

            transaction = {
                'transaction_id': str(uuid.uuid4()),
                'date': date_str,
                'merchant': description,  # Use description as merchant for bank statements
                'amount': amount,
                'category': category,
                'description': description,
                'transaction_type': 'debit' if amount < 0 else 'credit',
                'check_number': check_number,
                'bank': bank
            }
            transactions.append(transaction)

        # Insert into DuckDB
        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        for txn in transactions:
            db.execute_query("""
                INSERT INTO transactions (transaction_id, date, merchant, amount, category, description, transaction_type, account, check_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn['transaction_id'],
                txn['date'],
                txn['merchant'],
                txn['amount'],
                txn['category'],
                txn['description'],
                txn['transaction_type'],
                'Assets:Checking:MainBank',  # Default account
                txn.get('check_number', '')
            ))

        logger.info(f"Successfully ingested {len(transactions)} transactions from {bank}")

        return {
            "message": f"Successfully ingested {len(transactions)} transactions",
            "transactions_count": len(transactions),
            "bank": bank
        }

    except Exception as e:
        logger.error(f"Error ingesting CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@app.get("/transactions")
async def get_transactions(limit: int = 100, search: str = None):
    """Get all transactions with optional search."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        if search:
            query = """
                SELECT transaction_id, date, merchant, amount, category, description, transaction_type
                FROM transactions
                WHERE merchant LIKE ? OR category LIKE ? OR description LIKE ?
                ORDER BY date DESC
                LIMIT ?
            """
            transactions = db.execute_query(query, [f'%{search}%', f'%{search}%', f'%{search}%', limit]).fetchdf()
        else:
            query = """
                SELECT transaction_id, date, merchant, amount, category, description, transaction_type
                FROM transactions
                ORDER BY date DESC
                LIMIT ?
            """
            transactions = db.execute_query(query, [limit]).fetchdf()

        db.close()
        return {"transactions": transactions.to_dict('records'), "count": len(transactions)}
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/transactions/clear-all")
async def clear_all_transactions():
    """Clear ALL transactions from the database - USE WITH CAUTION!"""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        # Get count before deleting
        count_result = db.execute_query("SELECT COUNT(*) FROM transactions").fetchall()
        count = count_result[0][0] if count_result else 0

        # Delete all transactions
        db.execute_query("DELETE FROM transactions")
        db.close()

        logger.warning(f"⚠️ ALL TRANSACTIONS DELETED - {count} transactions removed from database")

        return {
            "message": "All transactions deleted successfully",
            "deleted_count": count
        }
    except Exception as e:
        logger.error(f"Error clearing all transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """Delete a transaction by ID."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))
        db.execute_query("DELETE FROM transactions WHERE transaction_id = ?", [transaction_id])
        db.close()

        return {"message": "Transaction deleted successfully", "transaction_id": transaction_id}
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, update: TransactionUpdate):
    """Update a transaction."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        # Build update query
        updates = []
        params = []

        if update.merchant is not None:
            updates.append("merchant = ?")
            params.append(update.merchant)
        if update.amount is not None:
            updates.append("amount = ?")
            params.append(update.amount)
        if update.category is not None:
            updates.append("category = ?")
            params.append(update.category)
        if update.description is not None:
            updates.append("description = ?")
            params.append(update.description)

        if not updates:
            return {"message": "No updates provided"}

        params.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = ?"
        db.execute_query(query, params)
        db.close()

        return {"message": "Transaction updated successfully", "transaction_id": transaction_id}
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), category: str = "general"):
    """Upload and process a financial document (PDF, image, or text)."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from documents.document_processor import DocumentProcessor
        from storage.duck import DuckDBManager

        # Initialize processor
        upload_dir = Path(__file__).parent / 'data' / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        processor = DocumentProcessor(storage_path=str(upload_dir))

        # Read file contents
        file_contents = await file.read()

        # Determine MIME type
        mime_type = file.content_type or 'text/plain'
        if file.filename.endswith('.txt'):
            mime_type = 'text/plain'
        elif file.filename.endswith('.pdf'):
            mime_type = 'application/pdf'
        elif file.filename.endswith(('.png', '.jpg', '.jpeg')):
            mime_type = 'image/jpeg'

        # Save uploaded file
        file_path, saved_filename = processor.save_uploaded_file(file_contents, file.filename)
        document_id = str(uuid.uuid4())

        # Process document
        result = processor.process_document(file_path, saved_filename, mime_type)
        full_text = result['full_text']
        chunks = result['chunks']
        page_count = result['page_count']

        # Store in database
        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        # Insert document metadata
        db.execute_query(
            """INSERT INTO documents (document_id, filename, category, file_path, full_text, page_count, upload_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [document_id, file.filename, category, file_path, full_text, page_count, datetime.now().isoformat()]
        )

        # Insert chunks
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            db.execute_query(
                """INSERT INTO document_chunks (chunk_id, document_id, chunk_index, text_content)
                   VALUES (?, ?, ?, ?)""",
                [chunk_id, document_id, i, chunk]
            )

        db.close()

        # Add to vector store
        from documents.document_processor import DocumentEmbeddings
        embeddings = DocumentEmbeddings()
        embeddings.add_document_chunks(document_id, chunks)

        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "page_count": page_count,
            "chunks": len(chunks),
            "message": "Document uploaded and processed successfully"
        }
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/documents/ask")
async def ask_document_question(request: DocumentAskRequest):
    """
    Intelligent Q&A with routing between vector search, web search, and LLM fallback.
    Uses BGE-small embeddings and Qdrant vector database.
    """
    try:
        import sys
        import requests
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from documents.document_processor import DocumentEmbeddings
        from documents.query_router import QueryRouter, SearchStrategy
        from storage.duck import DuckDBManager

        # Initialize router and embeddings
        router = QueryRouter(serpapi_key=os.getenv('SERPAPI_KEY'))
        embeddings = DocumentEmbeddings()

        # Check if user has documents
        doc_count = embeddings.count_documents()
        has_documents = doc_count > 0

        # Route the query
        routing_decision = router.route_query(request.question, has_documents=has_documents)
        strategy = routing_decision['strategy']

        logger.info(f"Query routed to: {strategy} (confidence: {routing_decision['confidence']:.2f})")

        context = ""
        sources = []
        strategy_used = strategy

        # Execute chosen strategy
        if strategy == SearchStrategy.VECTOR:
            # Vector search in documents
            search_results = embeddings.search(request.question, n_results=5)

            if search_results and len(search_results) > 0:
                db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))
                context_parts = []
                sources_set = set()

                for i, result in enumerate(search_results):
                    chunk_text = result['text']
                    metadata = result.get('metadata', {})
                    doc_id = metadata.get('document_id', '')
                    score = result.get('score', 0)

                    if doc_id and score > 0.3:  # Relevance threshold
                        doc_info = db.execute_query(
                            "SELECT filename, category FROM documents WHERE document_id = ?",
                            [doc_id]
                        ).fetchdf()

                        if not doc_info.empty:
                            filename = doc_info.iloc[0]['filename']
                            context_parts.append(f"[Source {i+1} - {filename}]: {chunk_text}")
                            sources_set.add(filename)

                db.close()
                context = "\n\n".join(context_parts)
                sources = list(sources_set)

                # Fallback to LLM if no good results
                if not context or len(sources) == 0:
                    strategy_used = SearchStrategy.LLM
                    logger.info("Vector search found no relevant results, falling back to LLM")

        elif strategy == SearchStrategy.HYBRID:
            # HYBRID: Combine DuckDB transaction data + Qdrant document search
            logger.info("Executing HYBRID query - combining DuckDB + Qdrant")

            # Part 1: Query DuckDB for transaction data
            db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))
            transaction_data = {}

            try:
                # Get summary statistics
                total_income_result = db.execute_query(
                    "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE amount > 0"
                ).fetchall()
                total_expenses_result = db.execute_query(
                    "SELECT COALESCE(ABS(SUM(amount)), 0) as total FROM transactions WHERE amount < 0"
                ).fetchall()

                if total_income_result and len(total_income_result) > 0:
                    transaction_data['total_income'] = total_income_result[0][0]
                if total_expenses_result and len(total_expenses_result) > 0:
                    transaction_data['total_expenses'] = total_expenses_result[0][0]

                # Get category breakdown
                category_result = db.execute_query(
                    "SELECT category, SUM(amount) as total FROM transactions GROUP BY category ORDER BY ABS(total) DESC LIMIT 5"
                ).fetchall()
                if category_result:
                    transaction_data['top_categories'] = [
                        {"category": row[0], "amount": row[1]} for row in category_result
                    ]

                logger.info(f"DuckDB data retrieved: {transaction_data}")
            except Exception as e:
                logger.warning(f"Could not retrieve transaction data from DuckDB: {e}")
                transaction_data = {}

            # Part 2: Vector search for form instructions
            search_results = embeddings.search(request.question, n_results=3)
            context_parts = []
            sources_set = set()

            if search_results and len(search_results) > 0:
                for i, result in enumerate(search_results):
                    chunk_text = result['text']
                    metadata = result.get('metadata', {})
                    doc_id = metadata.get('document_id', '')
                    score = result.get('score', 0)

                    if doc_id and score > 0.3:
                        doc_info = db.execute_query(
                            "SELECT filename, category FROM documents WHERE document_id = ?",
                            (doc_id,)
                        ).fetchall()

                        if doc_info and len(doc_info) > 0:
                            filename = doc_info[0][0]
                            sources_set.add(filename)
                            context_parts.append(f"Source {i+1} ({filename}):\n{chunk_text}\n")

                context = "\n".join(context_parts)
                sources = list(sources_set)
            else:
                context = ""
                sources = []

            # Build combined context
            if transaction_data:
                data_summary = "YOUR TRANSACTION DATA:\n"
                if 'total_income' in transaction_data:
                    data_summary += f"Total Income: ${transaction_data['total_income']:,.2f}\n"
                if 'total_expenses' in transaction_data:
                    data_summary += f"Total Expenses: ${transaction_data['total_expenses']:,.2f}\n"
                if 'top_categories' in transaction_data:
                    data_summary += "\nTop Spending Categories:\n"
                    for cat in transaction_data['top_categories']:
                        data_summary += f"  - {cat['category']}: ${abs(cat['amount']):,.2f}\n"
                data_summary += "\n"
                context = data_summary + context

            strategy_used = SearchStrategy.HYBRID

        elif strategy == SearchStrategy.WEB:
            # Web search via SerpAPI
            web_results = router.search_web(request.question, num_results=5)

            if web_results:
                context = router.format_web_context(web_results)
                sources = router.extract_sources(web_results)
            else:
                # Fallback to LLM if web search fails
                strategy_used = SearchStrategy.LLM
                logger.info("Web search failed, falling back to LLM")

        # Prepare prompt based on strategy used
        if strategy_used == SearchStrategy.HYBRID:
            system_prompt = f"""<|im_start|>system
You are a financial tax advisor. You have access to both the user's ACTUAL transaction data from their database AND form instructions from their uploaded documents.

Combine both sources to provide a complete, accurate answer with specific numbers from their data.<|im_end|>
<|im_start|>user
{context}

Question: {request.question}

Answer with:
1. The exact numbers from their transaction data
2. How to report those numbers according to the form instructions
3. Which specific forms/lines to use

Be detailed and cite both data sources and document sources.<|im_end|>
<|im_start|>assistant
"""

        elif strategy_used == SearchStrategy.VECTOR:
            system_prompt = f"""<|im_start|>system
You are a financial document analyst. Answer the question based ONLY on the provided document excerpts. If the answer isn't in the documents, say so.<|im_end|>
<|im_start|>user
Document Context:
{context}

Question: {request.question}

Answer (be specific and cite sources):<|im_end|>
<|im_start|>assistant
"""

        elif strategy_used == SearchStrategy.WEB:
            system_prompt = f"""<|im_start|>system
You are a knowledgeable financial advisor. Answer the question based on the web search results provided. Be factual and cite sources.<|im_end|>
<|im_start|>user
Web Search Results:
{context}

Question: {request.question}

Answer (be specific and cite sources):<|im_end|>
<|im_start|>assistant
"""

        else:  # LLM fallback
            system_prompt = f"""<|im_start|>system
You are a knowledgeable financial advisor. Provide helpful advice on personal finance, budgeting, debt management, taxes, savings, and investments. Be concise (2-4 sentences).<|im_end|>
<|im_start|>user
Question: {request.question}

Answer:<|im_end|>
<|im_start|>assistant
"""

        # Call LLM
        hermes_url = os.getenv('HERMES_URL', 'http://127.0.0.1:11434')

        try:
            health_response = requests.get(f"{hermes_url}/health", timeout=2)
            if health_response.status_code != 200:
                raise HTTPException(status_code=503, detail="AI advisor not available")
        except:
            raise HTTPException(status_code=503, detail="AI advisor not available")

        payload = {
            "prompt": system_prompt,
            "max_tokens": 600,
            "temperature": 0.3 if strategy_used != SearchStrategy.LLM else 0.7,
            "stop": ["</s>", "<|im_end|>", "###"],
            "stream": False
        }

        logger.info(f"Sending prompt to LLM (length: {len(system_prompt)} chars, ~{len(system_prompt.split())} words)")
        logger.info(f"Prompt starts with: {system_prompt[:200]}...")
        logger.info(f"Prompt ends with: ...{system_prompt[-200:]}")

        response = requests.post(f"{hermes_url}/completion", json=payload, timeout=30)

        logger.info(f"LLM response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"LLM response data keys: {data.keys()}")
            logger.info(f"LLM stop type: {data.get('stop_type')}, stopping_word: {data.get('stopping_word')}")
            logger.info(f"LLM tokens_predicted: {data.get('tokens_predicted')}")
            content = data.get('content', '').strip()
            logger.info(f"LLM content: '{content}'")
            logger.info(f"LLM content length: {len(content)}")
            return {
                "answer": content,
                "sources": sources,
                "strategy": strategy_used,
                "routing_confidence": routing_decision['confidence'],
                "success": True
            }
        else:
            logger.error(f"LLM failed with status {response.status_code}: {response.text}")
            raise HTTPException(status_code=500, detail="AI generation failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document Q&A: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        query = """
            SELECT document_id, filename, category, page_count, upload_date
            FROM documents
            ORDER BY upload_date DESC
        """
        documents = db.execute_query(query).fetchdf()
        db.close()

        return {
            "documents": documents.to_dict('records'),
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'personal-finance'))
        from storage.duck import DuckDBManager
        from documents.document_processor import DocumentEmbeddings

        db = DuckDBManager(db_path=str(Path(__file__).parent / 'data' / 'finance.db'))

        # Delete from vector store
        embeddings = DocumentEmbeddings()
        embeddings.delete_document(document_id)

        # Delete chunks
        db.execute_query("DELETE FROM document_chunks WHERE document_id = ?", [document_id])

        # Delete document
        db.execute_query("DELETE FROM documents WHERE document_id = ?", [document_id])

        db.close()

        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id
        }
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Mount static files and frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    # Serve static files (CSS, JS)
    static_path = frontend_path / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Serve index.html at root
    @app.get("/")
    async def read_root():
        """Serve the frontend UI."""
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found. API available at /docs"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Personal Finance API on http://127.0.0.1:8000")
    print("📝 Simplified server for testing without database dependencies")
    print()

    # Check for frontend
    frontend_path = Path(__file__).parent / "frontend"
    if frontend_path.exists():
        print("✅ Frontend UI: http://127.0.0.1:8000/")
    else:
        print("⚠️  Frontend not found - UI not available")

    print("✅ API Documentation: http://127.0.0.1:8000/docs")
    print()

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
