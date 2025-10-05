# 📄 Document Upload & Question Answering - Implementation Plan

## Overview
Add ability to upload financial documents (PDFs, bank statements, tax forms) and ask questions about them using AI.

## Architecture

### 1. Document Storage
```
data/
├── documents/              # Uploaded files
│   ├── bank_statements/
│   ├── tax_documents/
│   └── receipts/
└── document_index.db      # Document metadata and extracted text
```

### 2. Document Processing Pipeline
1. **Upload** → User uploads PDF/image/text file
2. **Extract** → Extract text from document (PDF, OCR for images)
3. **Index** → Store document chunks in database with metadata
4. **Query** → User asks question
5. **Retrieve** → Find relevant document chunks
6. **Generate** → LLM answers using retrieved context

### 3. Technologies Needed

**Current (Simple):**
- PyPDF2 (already in requirements) - Extract text from PDFs
- Store text in DuckDB with full-text search
- Pass relevant chunks to LLM

**Future (Advanced):**
- Embedding models for semantic search
- Vector database (ChromaDB, FAISS)
- OCR for scanned documents (Tesseract)

## Implementation (Simple Version)

### Step 1: Add Document Upload Endpoint
```python
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    category: str = "general",
    description: str = ""
):
    # Save file
    # Extract text
    # Store in database
    # Return document ID
```

### Step 2: Add Document Query Endpoint
```python
@app.post("/documents/ask")
async def ask_about_documents(
    question: str,
    document_ids: Optional[List[str]] = None
):
    # Search for relevant text chunks
    # Construct prompt with context
    # Get LLM answer
    # Return answer with sources
```

### Step 3: Add UI Tab
- Document upload section
- List of uploaded documents
- Chat interface for document Q&A
- Source citations

## Example Use Cases

1. **Bank Statement Analysis**
   - Upload: January bank statement PDF
   - Ask: "What were my largest expenses this month?"
   - AI: "Based on your bank statement, your largest expenses were..."

2. **Tax Document Review**
   - Upload: W-2, 1099 forms
   - Ask: "How much did I earn from freelance work?"
   - AI: "According to your 1099-MISC, you earned $15,000..."

3. **Receipt Management**
   - Upload: Multiple receipt images
   - Ask: "How much did I spend on office supplies?"
   - AI: "From your receipts, office supplies totaled $247.32..."

4. **Multi-Document Questions**
   - Upload: Multiple statements
   - Ask: "Compare my spending from January vs February"
   - AI: "January spending was $3,200 vs February at $2,800..."

## Database Schema

```sql
CREATE TABLE documents (
    document_id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    category VARCHAR,
    description TEXT,
    file_path VARCHAR,
    file_size INTEGER,
    mime_type VARCHAR,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_text TEXT,
    page_count INTEGER,
    metadata JSON
);

CREATE TABLE document_chunks (
    chunk_id VARCHAR PRIMARY KEY,
    document_id VARCHAR,
    chunk_index INTEGER,
    text_content TEXT,
    page_number INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
```

## Security Considerations

1. **File Validation**
   - Check file types (PDF, PNG, JPG only)
   - Limit file sizes (e.g., 10MB max)
   - Scan for malicious content

2. **Data Privacy**
   - Store locally only
   - No cloud uploads
   - Encrypted storage optional

3. **Access Control**
   - User authentication (future)
   - Document permissions

## Would you like me to implement this now?

I can create:
1. ✅ Document upload API endpoint
2. ✅ Document Q&A endpoint
3. ✅ Web UI tab for document management
4. ✅ PDF text extraction
5. ✅ Database schema for documents
6. ✅ Chat interface for document questions

**Estimated time: 15-20 minutes**

Let me know if you want me to proceed!
