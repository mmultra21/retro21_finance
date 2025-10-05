-- Document RAG Schema for DuckDB

-- Drop existing tables if they exist
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS documents;

-- Create documents table
CREATE TABLE documents (
    document_id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    category VARCHAR DEFAULT 'general',
    file_path VARCHAR NOT NULL,
    full_text TEXT,
    page_count INTEGER DEFAULT 1,
    upload_date VARCHAR
);

-- Create document chunks table for RAG
CREATE TABLE document_chunks (
    chunk_id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL
);

-- Create indexes
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
