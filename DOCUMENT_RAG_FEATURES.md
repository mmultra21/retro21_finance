# Document RAG System - Enhanced Features

## 🎯 Overview
Complete rebuild of the Document Management & Q&A system with intelligent routing, source indicators, and vector store management.

## ✨ New Features

### 1. **Real-time Vector Store Statistics**
- **Documents Count**: Live count of indexed documents
- **Last Strategy**: Shows which routing strategy was used (VECTOR/WEB/LLM)
- **Query Counter**: Tracks total queries processed

### 2. **Intelligent Query Routing**
The system automatically routes queries to the best strategy:

#### 📄 VECTOR Strategy
- **When**: Questions about uploaded documents (personal pronouns + financial keywords)
- **Example**: "Based on my bank statement, how should I report this income on IRS Form 1040?"
- **Sources**: Your uploaded documents via semantic search in Qdrant
- **Badge Color**: Green

#### 🌐 WEB Strategy
- **When**: Time-sensitive queries needing current information
- **Example**: "What are the current mortgage rates today?"
- **Sources**: SerpAPI web search
- **Badge Color**: Blue

#### 🤖 LLM Strategy
- **When**: General financial advice without specific data needs
- **Example**: "What are some general tips for saving money?"
- **Sources**: Hermes3 LLM knowledge
- **Badge Color**: Orange

### 3. **Enhanced Document Display**
- **Status Indicator**: Shows "● Indexed" for all vectorized documents
- **Category Badges**: Tax, Bank, Investment, IRA, etc.
- **Vector Store Info**: Clear indication documents are searchable
- **Export Function**: Download document list as CSV

### 4. **Source Citation System**
Every answer includes:
- **Source Badge**: Visual indicator of routing strategy
- **Source List**: All documents used to generate the answer
- **Routing Confidence**: Percentage confidence in routing decision
- **Detailed Metadata**: Full transparency on how answer was generated

### 5. **Use Case Examples**
Built-in examples for common scenarios:

```
🏦→📄 "Based on my bank statement, how should I report this income on IRS Form 1040?"
→ Routes to VECTOR, searches your uploaded bank statements and tax forms

📊→📄 "What IRA contribution limits apply to my situation according to the uploaded tax documents?"
→ Routes to VECTOR, finds IRA information in your documents

💰→📄 "How do I calculate my estimated tax payments using my income records?"
→ Routes to VECTOR, uses your income documents

🌐 "What are the current mortgage rates today?"
→ Routes to WEB, fetches live data via SerpAPI
```

## 🔧 Technical Implementation

### Frontend Components
- **HTML**: Enhanced UI with stat badges, routing info, and source displays
- **CSS**: New styles for badges, sources list, and enhanced messages
- **JavaScript**: Complete rewrite with state tracking and enhanced formatting

### Files Modified
1. `frontend/index.html` - Rebuilt Documents tab
2. `frontend/static/css/style.css` - Added RAG-specific styles
3. `frontend/static/js/documents.js` - Complete rewrite with routing display

### API Integration
- **Upload**: `POST /documents/upload` - Vectorizes and stores in Qdrant
- **Query**: `POST /documents/ask` - Intelligent routing with source tracking
- **List**: `GET /documents` - Get all documents from vector store
- **Delete**: `DELETE /documents/{id}` - Remove from vector store

## 📊 Tested Scenarios

### Vector Search (WORKING ✅)
```bash
Query: "Based on my tax documents, what were my total retirement contributions?"
Response:
  - Strategy: VECTOR
  - Confidence: 90%
  - Sources: test_tax_document.txt, i1040gi.pdf
  - Answer: $33,650 (401k: $23K, IRA: $6.5K, HSA: $4.15K)
```

### LLM Fallback (WORKING ✅)
```bash
Query: "What are some general tips for saving money?"
Response:
  - Strategy: LLM
  - Confidence: 70%
  - Sources: []
  - Answer: Budget tips, automation, expense tracking
```

## 🚀 Usage

### Upload Documents
1. Select category (Tax, Bank, IRA, etc.)
2. Choose file (PDF, Image, or Text)
3. Click "Upload & Vectorize"
4. Document is processed and added to Qdrant

### Ask Questions
1. Type question in text area
2. System automatically routes to best strategy
3. View answer with source indicators
4. See which documents were used
5. Check routing confidence

### Manage Documents
1. View all documents in vector store
2. See indexed status
3. Export list as CSV
4. Delete individual documents

## 🎨 Visual Indicators

### Source Badges
- 📄 **VECTOR** - Green badge - Document search
- 🌐 **WEB** - Blue badge - Web search
- 🤖 **LLM** - Orange badge - Direct AI

### Document Status
- ● **Indexed** - Green dot - Ready for search
- Upload Date - When vectorized
- Page Count - Total pages processed

## 🔍 Real-World Use Case

**Scenario**: You have uploaded:
- Your bank statement (PDF)
- IRS Form 1040 instructions (PDF)
- Your previous year tax return (PDF)

**Query**: "Based on my bank statement showing $5,000 monthly income, how should I report this on Form 1040 and what are my IRA contribution limits?"

**System Response**:
1. Routes to **VECTOR** strategy (90% confidence)
2. Searches all 3 documents
3. Finds relevant sections about income reporting and IRA limits
4. Generates answer citing specific sections
5. Shows sources: bank_statement.pdf, i1040gi.pdf
6. Displays routing info and confidence

## 📝 Notes

- **Context Window**: Hermes3 configured with 8192 tokens (handles large document contexts)
- **Embeddings**: BGE-small-en-v1.5 for semantic search
- **Vector DB**: Qdrant with persistent storage
- **Cache Busting**: Timestamp-based (t=1759641817)

## 🔄 Browser Cache
After deployment, hard refresh your browser:
- **Chrome/Edge**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
- **Firefox**: Cmd+Shift+R (Mac) or Ctrl+F5 (Windows)
- **Safari**: Cmd+Option+R (Mac)

Or use DevTools → Right-click refresh → "Empty Cache and Hard Reload"
