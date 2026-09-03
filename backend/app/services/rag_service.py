import hashlib
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pgvector.sqlalchemy import Vector
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.services.embedding_service import EmbeddingService

class RAGService:
    """
    Production-Quality RAG Pipeline using pgvector.
    Supports chunking, semantic retrieval, and metadata filtering.
    """

    @staticmethod
    def _chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunker based on characters."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + max_chunk_size
            
            # Try to snap to nearest paragraph or sentence boundary if possible
            if end < text_length:
                snap_end = text.rfind("\n\n", start, end)
                if snap_end == -1:
                    snap_end = text.rfind(". ", start, end)
                if snap_end != -1 and snap_end > start + (max_chunk_size // 2):
                    end = snap_end + 1
                    
            chunks.append(text[start:end].strip())
            start = end - overlap
            
        return [c for c in chunks if c]

    @staticmethod
    async def ingest_document(
        db: AsyncSession,
        title: str,
        content: str,
        source: str,
        document_type: str,
        topic: str,
        region: Optional[str] = None
    ) -> KnowledgeDocument:
        """
        Ingests a document, chunks it, generates embeddings, and stores in pgvector.
        Prevents duplicate ingestion via content hash.
        """
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Check for duplicates
        existing = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.content_hash == content_hash))
        doc = existing.scalar_one_or_none()
        if doc:
            return doc # Already ingested
            
        # Create Document
        doc = KnowledgeDocument(
            title=title,
            source=source,
            document_type=document_type,
            topic=topic,
            region=region,
            content_hash=content_hash
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        # Chunking
        chunks = RAGService._chunk_text(content)
        
        # Generating Embeddings (batch)
        embeddings = EmbeddingService.get_embeddings(chunks)
        
        # Storing Chunks
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk_text,
                embedding=embedding,
                metadata_json={
                    "char_length": len(chunk_text),
                    "model": "all-MiniLM-L6-v2",
                    "dimension": len(embedding)
                }
            )
            db.add(chunk)
            
        await db.commit()
        return doc

    @staticmethod
    async def retrieve_evidence(
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Top-K semantic retrieval using pgvector cosine distance.
        """
        query_vector = EmbeddingService.get_embedding(query)
        
        # Distance metric (Cosine distance = 1 - Cosine Similarity)
        # Using l2_distance or cosine_distance. Vector.cosine_distance is built-in to pgvector-sqlalchemy
        
        stmt = select(DocumentChunk, KnowledgeDocument, DocumentChunk.embedding.cosine_distance(query_vector).label("distance")) \
            .join(KnowledgeDocument)
            
        if filters:
            conditions = []
            if "region" in filters and filters["region"]:
                conditions.append(or_(KnowledgeDocument.region == filters["region"], KnowledgeDocument.region == None))
            if "document_type" in filters and filters["document_type"]:
                conditions.append(KnowledgeDocument.document_type == filters["document_type"])
            if "topic" in filters and filters["topic"]:
                conditions.append(KnowledgeDocument.topic == filters["topic"])
                
            if conditions:
                stmt = stmt.where(and_(*conditions))
                
        # We order by distance ascending (smaller distance = higher similarity)
        stmt = stmt.order_by("distance").limit(top_k)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        evidence = []
        for chunk, doc, distance in rows:
            similarity = 1.0 - float(distance)
            if similarity >= similarity_threshold:
                evidence.append({
                    "document_id": doc.id,
                    "chunk_id": chunk.id,
                    "similarity_score": round(similarity, 3),
                    "title": doc.title,
                    "source": doc.source,
                    "document_type": doc.document_type,
                    "region": doc.region,
                    "excerpt": chunk.content
                })
                
        return evidence
