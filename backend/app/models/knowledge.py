from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String)
    document_type = Column(String) # e.g., "GUIDELINE", "METHODOLOGY", "RESEARCH"
    topic = Column(String)
    publication_date = Column(DateTime)
    region = Column(String, nullable=True) # Applicable region if any
    content_hash = Column(String, unique=True, index=True) # Prevent duplicate ingestion
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    
    content = Column(Text)
    
    # We will use 384 for all-MiniLM-L6-v2. If model changes, we migrate.
    embedding = Column(Vector(384))
    
    metadata_json = Column(JSON, default={}) # Store extra fields if needed
    
    document = relationship("KnowledgeDocument", back_populates="chunks")
