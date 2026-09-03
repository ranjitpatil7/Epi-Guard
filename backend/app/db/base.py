from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.domain import *
from app.models.copilot import *
from app.models.knowledge import KnowledgeDocument, DocumentChunk
