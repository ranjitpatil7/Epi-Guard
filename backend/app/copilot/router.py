from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.copilot.schemas import CopilotRequest, CopilotResponse, ExplainRiskRequest, ExplainRiskResponse
from app.copilot.service import process_copilot_message, get_conversations, get_conversation_history
from app.copilot.safety import SafetyViolation
from app.copilot.provider import get_llm_provider
import json
from app.core.auth_deps import get_current_user
from app.models.users import User

router = APIRouter()

@router.post("/explain-risk", response_model=ExplainRiskResponse)
async def explain_risk(request: ExplainRiskRequest):
    """Generates a natural language summary of SHAP contributing factors."""
    try:
        provider = get_llm_provider()
        prompt = "You are an expert AI epidemiologist. Your job is to read SHAP feature attributions and explain them to a user."
        messages = [{
            "role": "user",
            "content": f"Based on these SHAP values indicating feature importance for a risk model: {json.dumps(request.contributing_factors)}, explain in ONE natural language sentence what is the primary driver of the elevated risk. Do not use technical jargon like 'SHAP values'. For example: 'The primary driver of the elevated risk is the recent deterioration in water quality combined with an increase in community disease reports.'"
        }]
        
        response_text, _ = await provider.generate_response(
            system_prompt=prompt,
            messages=messages
        )
        return ExplainRiskResponse(explanation=response_text.strip())
    except Exception:
        # Graceful fallback: generate a template-based explanation from the raw factors
        factors = request.contributing_factors
        if factors and len(factors) > 0:
            # Sort by impact (descending) if they have an 'impact' field
            sorted_factors = sorted(factors, key=lambda f: abs(f.get("impact", 0)) if isinstance(f, dict) else 0, reverse=True)
            top = sorted_factors[0]
            feature_name = top.get("feature", "unknown factor") if isinstance(top, dict) else str(top)
            explanation = f"The primary driver of the elevated risk is {feature_name.replace('_', ' ')}."
            if len(sorted_factors) > 1:
                second = sorted_factors[1]
                second_name = second.get("feature", "another factor") if isinstance(second, dict) else str(second)
                explanation += f" This is compounded by {second_name.replace('_', ' ')}."
        else:
            explanation = "Risk factors could not be determined from the available data."
        return ExplainRiskResponse(explanation=explanation)

@router.post("/chat", response_model=CopilotResponse)
async def chat(request: CopilotRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Legacy backward-compatible chat endpoint."""
    try:
        response = await process_copilot_message(db, request, current_user.id)
        return response
    except SafetyViolation as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/investigate", response_model=CopilotResponse)
async def investigate(request: CopilotRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Advanced Agentic Investigation Endpoint."""
    try:
        response = await process_copilot_message(db, request, current_user.id)
        return response
    except SafetyViolation as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{conversation_id}")
async def get_investigation_trace(conversation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieves the agent trace for the last message in a conversation."""
    try:
        history = await get_conversation_history(db, conversation_id, current_user.id)
        if not history:
            return []
        last_msg = history[-1]
        if last_msg.role == "model" and last_msg.structured_response:
            return last_msg.structured_response.get("agent_trace", [])
        return []
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")

@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    convs = await get_conversations(db, current_user.id)
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at} for c in convs]

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        history = await get_conversation_history(db, conversation_id, current_user.id)
        return [{"role": msg.role, "content": msg.content, "structured_response": msg.structured_response} for msg in history]
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
