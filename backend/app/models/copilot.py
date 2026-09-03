from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class CopilotConversation(Base):
    __tablename__ = "copilot_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    title = Column(String, nullable=True)

    messages = relationship("CopilotMessage", back_populates="conversation", cascade="all, delete-orphan")

class CopilotMessage(Base):
    __tablename__ = "copilot_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("copilot_conversations.id", ondelete="CASCADE"))
    role = Column(String, index=True) # user, model, tool, system
    content = Column(Text, nullable=True)
    tool_calls = Column(JSON, nullable=True) # List of dicts representing tool calls made by the assistant
    structured_response = Column(JSON, nullable=True) # The final CopilotResponse parsed JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("CopilotConversation", back_populates="messages")
