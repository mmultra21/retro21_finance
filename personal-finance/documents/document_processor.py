"""
Document processing for RAG (Retrieval-Augmented Generation).
Handles PDF extraction, OCR, chunking, and embedding.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process documents for RAG Q&A."""

    def __init__(self, storage_path: str = "data/documents"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> tuple[str, int]:
        """Extract text from PDF file."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(pdf_path)
            text = ""
            page_count = len(reader.pages)

            for page in reader.pages:
                text += page.extract_text() + "\n\n"

            return text.strip(), page_count
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR error: {e}")
            # Return empty if OCR fails (Tesseract might not be installed)
            return ""

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for better retrieval."""
        if not text:
            return []

        chunks = []
        words = text.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def process_document(self, file_path: str, filename: str, mime_type: str) -> Dict[str, Any]:
        """Process uploaded document and extract text."""
        try:
            # Extract text based on file type
            if mime_type == "application/pdf":
                full_text, page_count = self.extract_text_from_pdf(file_path)
            elif mime_type in ["image/png", "image/jpeg", "image/jpg"]:
                full_text = self.extract_text_from_image(file_path)
                page_count = 1
            elif mime_type == "text/plain":
                with open(file_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                page_count = 1
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")

            # Chunk the text
            chunks = self.chunk_text(full_text)

            return {
                "full_text": full_text,
                "page_count": page_count,
                "chunks": chunks,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise

    def save_uploaded_file(self, file_data: bytes, original_filename: str) -> tuple[str, str]:
        """Save uploaded file and return path and new filename."""
        # Generate unique filename
        file_ext = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = self.storage_path / unique_filename

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)

        return str(file_path), unique_filename


class DocumentEmbeddings:
    """Handle document embeddings for semantic search using BGE-small and Qdrant."""

    def __init__(self, collection_name: str = "financial_documents"):
        self.collection_name = collection_name
        self._client = None
        self._embedding_model = None
        self._vector_size = 384  # BGE-small-en-v1.5 produces 384-dim vectors

    def _initialize(self):
        """Lazy initialization of embedding model and vector store."""
        if self._client is not None:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            from sentence_transformers import SentenceTransformer

            # Initialize Qdrant with persistent storage
            qdrant_path = Path("data/qdrant_db")
            qdrant_path.mkdir(parents=True, exist_ok=True)

            self._client = QdrantClient(path=str(qdrant_path))

            # Create collection if it doesn't exist
            collections = self._client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)

            if not collection_exists:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self._vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

            # Initialize BGE-small embedding model
            self._embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')

            logger.info("Qdrant and BGE-small initialized successfully")
        except Exception as e:
            logger.error(f"Embedding initialization error: {e}")
            raise

    def add_document_chunks(self, document_id: str, chunks: List[str], metadata: Optional[List[Dict]] = None):
        """Add document chunks to Qdrant vector store."""
        self._initialize()

        if not chunks:
            return

        from qdrant_client.models import PointStruct
        import uuid

        # Generate embeddings for all chunks
        embeddings = self._embedding_model.encode(chunks, show_progress_bar=False)

        # Prepare metadata
        if metadata is None:
            metadata = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

        # Create points for Qdrant
        points = []
        for i, (chunk, embedding, meta) in enumerate(zip(chunks, embeddings, metadata)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_chunk_{i}"))

            points.append(PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    **meta,
                    "text": chunk,
                    "chunk_id": f"{document_id}_chunk_{i}"
                }
            ))

        # Upsert points to Qdrant
        self._client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(f"Added {len(chunks)} chunks for document {document_id} to Qdrant")

    def search(self, query: str, n_results: int = 5, document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using Qdrant."""
        self._initialize()

        from qdrant_client.models import Filter, FieldCondition, MatchAny

        # Encode query
        query_embedding = self._embedding_model.encode(query, show_progress_bar=False)

        # Build filter if document_ids specified
        query_filter = None
        if document_ids:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=document_ids)
                    )
                ]
            )

        # Search in Qdrant
        search_results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=n_results,
            query_filter=query_filter
        )

        # Format results
        formatted_results = []
        for hit in search_results:
            formatted_results.append({
                "text": hit.payload.get("text", ""),
                "metadata": {
                    "document_id": hit.payload.get("document_id", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                    "chunk_id": hit.payload.get("chunk_id", "")
                },
                "score": hit.score,
                "distance": 1.0 - hit.score  # Convert similarity to distance
            })

        logger.info(f"Found {len(formatted_results)} results for query")
        return formatted_results

    def delete_document(self, document_id: str):
        """Delete all chunks for a document from Qdrant."""
        self._initialize()

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        try:
            # Delete all points with matching document_id
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted chunks for document {document_id} from Qdrant")
        except Exception as e:
            logger.warning(f"Error deleting document chunks: {e}")

    def count_documents(self) -> int:
        """Count total number of points in the collection."""
        self._initialize()

        try:
            collection_info = self._client.get_collection(self.collection_name)
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
