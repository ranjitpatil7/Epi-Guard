import json
import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.copilot import CopilotConversation, CopilotMessage
from app.copilot.schemas import CopilotRequest, CopilotResponse
from app.copilot.safety import check_query_safety
from app.copilot.provider import get_llm_provider
from app.copilot.tools import ToolRegistry
from app.copilot.audit import log_copilot_action
from app.copilot.stream import broadcast_copilot_event
from app.realtime.ws_events import WSEventType
import logging
import uuid

logger = logging.getLogger(__name__)

# System prompt forcing JSON output for tool execution or final response
ORCHESTRATOR_PROMPT = """You are the Intelligence Agent Orchestrator for JalRakshak AI.
Your goal is to investigate public health signals using your specialized tools.
You MUST output valid JSON ONLY. Do not write normal text.
If you need to use a tool, return:
{
    "action": "use_tool",
    "tool_name": "risk_analyst",
    "tool_arguments": {"region_name": "assam"},
    "reasoning": "I need to check the risk score first."
}

Available Tools:
1. risk_analyst: args {"region_name": "str"}
2. spatial_analyst: args {"region_name": "str"}
3. scenario_analyst: args {"region_name": "str", "changes": {"feature": float}}
4. evidence_researcher: args {"query": "str", "region": "str"}
5. data_quality_analyst: args {"region_name": "str"}

If you have enough information to answer the user's query, return the final response matching exactly this schema:
{
    "action": "final_response",
    "executive_summary": "string",
    "estimated_risk": float,
    "risk_level": "string",
    "prediction_interval": {"lower": float, "upper": float},
    "confidence": float,
    "contributing_factors": ["string"],
    "retrieved_evidence": [{"source": "str", "excerpt": "str"}],
    "scenario_results": {},
    "data_quality": 0.0,
    "limitations": "string",
    "disclaimer": "SYNTHETIC DEMONSTRATION DATA. NON-DIAGNOSTIC."
}

Do NOT invent risk scores, statistics, or evidence. If the tools did not provide it, say 'Insufficient evidence available'.
"""

async def process_copilot_message(db: AsyncSession, request: CopilotRequest, user_id: int) -> CopilotResponse:
    global_start = time.perf_counter()
    
    # 1. Safety Check (Pre-execution)
    check_query_safety(request.message)

    request_id = request.request_id or str(uuid.uuid4())
    sequence_number = 0

    def get_safe_thinking_message(tool: str) -> str:
        safe_messages = {
            "risk_analyst": "Analyzing regional risk metrics",
            "spatial_analyst": "Evaluating spatial propagation patterns",
            "scenario_analyst": "Running risk scenario simulation",
            "evidence_researcher": "Retrieving relevant evidence",
            "data_quality_analyst": "Checking regional data quality",
            "get_active_incidents": "Retrieving active incidents",
            "get_incident_details": "Reviewing incident evidence",
            "investigate_incident": "Investigating incident context",
            "get_risk_history": "Comparing historical risk snapshots",
            "get_latest_risk_snapshot": "Retrieving latest risk evaluation",
            "get_alert_details": "Reviewing alert details",
            "get_risk_lineage": "Tracing risk calculation lineage"
        }
        return safe_messages.get(tool, "Evaluating deterministic risk information")

    # 2. Setup Conversation Context
    if request.conversation_id:
        conv = await db.get(CopilotConversation, request.conversation_id)
        if not conv or conv.user_id != user_id:
            raise ValueError("Conversation not found")
    else:
        conv = CopilotConversation(user_id=user_id, title=request.message[:50])
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # Save user message
    user_msg = CopilotMessage(conversation_id=conv.id, role="user", content=request.message)
    db.add(user_msg)
    
    # Fetch User for auth
    from app.models.users import User
    user = await db.get(User, user_id)
    
    await db.commit()

    registry = ToolRegistry(db, user)
    provider = get_llm_provider()
    
    sequence_number += 1
    await broadcast_copilot_event(
        WSEventType.COPILOT_REQUEST_STARTED,
        conv.id, request_id, sequence_number,
        {"message": "Investigation started"},
        user_id
    )

    # 3. Bounded ReAct Execution Loop
    max_iterations = 5
    iteration = 0
    
    # Start with the orchestrator prompt and user query
    messages = [{"role": "user", "content": request.message}]
    
    # Observability Trace
    agent_trace = []
    tools_used = []
    final_response_json = None

    try:

        while iteration < max_iterations:
            iteration += 1
            
            sequence_number += 1
            await broadcast_copilot_event(
                WSEventType.AGENT_THINKING,
                conv.id, request_id, sequence_number,
                {"status": "Synthesizing next steps..."},
                user_id
            )

            # Call LLM
            content_str, _ = await provider.generate_response(
                system_prompt=ORCHESTRATOR_PROMPT,
                messages=messages,
                response_schema=None # We parse the raw JSON dict ourselves in this loop
            )
            
            try:
                # Parse LLM JSON decision
                # Sometimes models wrap JSON in markdown block
                if "```json" in content_str:
                    content_str = content_str.split("```json")[1].split("```")[0].strip()
                elif "```" in content_str:
                    content_str = content_str.split("```")[1].split("```")[0].strip()
                    
                decision = json.loads(content_str)
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON: {content_str}")
                agent_trace.append({"error": "LLM returned invalid JSON"})
                break
                
            action = decision.get("action")
            
            if action == "final_response":
                sequence_number += 1
                await broadcast_copilot_event(
                    WSEventType.AGENT_SYNTHESIS_STARTED,
                    conv.id, request_id, sequence_number,
                    {"status": "Preparing final synthesis"},
                    user_id
                )
                final_response_json = decision
                agent_trace.append({"action": "final_synthesis", "status": "complete"})
                sequence_number += 1
                await broadcast_copilot_event(
                    WSEventType.FINAL_SYNTHESIS,
                    conv.id, request_id, sequence_number,
                    {"status": "Final synthesis complete"},
                    user_id
                )
                break
                
            elif action == "use_tool":
                tool_name = decision.get("tool_name")
                tool_args = decision.get("tool_arguments", {})
                reasoning = decision.get("reasoning", "")
                
                sequence_number += 1
                await broadcast_copilot_event(
                    WSEventType.TOOL_SELECTED,
                    conv.id, request_id, sequence_number,
                    {"tool_name": tool_name},
                    user_id
                )

                sequence_number += 1
                safe_thinking_msg = get_safe_thinking_message(tool_name)
                await broadcast_copilot_event(
                    WSEventType.AGENT_THINKING,
                    conv.id, request_id, sequence_number,
                    {"status": safe_thinking_msg},
                    user_id
                )

                sequence_number += 1
                if tool_name == "evidence_researcher":
                    await broadcast_copilot_event(
                        WSEventType.RAG_RETRIEVAL_STARTED,
                        conv.id, request_id, sequence_number,
                        {"tool_name": tool_name},
                        user_id
                    )
                else:
                    await broadcast_copilot_event(
                        WSEventType.TOOL_EXECUTION_STARTED,
                        conv.id, request_id, sequence_number,
                        {"tool_name": tool_name},
                        user_id
                    )

                # Execute tool safely
                tool_res = await registry.execute_tool(tool_name, tool_args)
                
                sequence_number += 1
                if not tool_res.success:
                    await broadcast_copilot_event(
                        WSEventType.TOOL_EXECUTION_FAILED,
                        conv.id, request_id, sequence_number,
                        {"tool_name": tool_name, "error": tool_res.error},
                        user_id
                    )
                else:
                    if tool_name == "evidence_researcher":
                        await broadcast_copilot_event(
                            WSEventType.RAG_RETRIEVAL_COMPLETED,
                            conv.id, request_id, sequence_number,
                            {"tool_name": tool_name, "latency_ms": tool_res.execution_time_ms},
                            user_id
                        )
                        sequence_number += 1
                        await broadcast_copilot_event(
                            WSEventType.EVIDENCE_RETRIEVED,
                            conv.id, request_id, sequence_number,
                            {"tool_name": tool_name},
                            user_id
                        )
                    else:
                        await broadcast_copilot_event(
                            WSEventType.TOOL_EXECUTION_COMPLETED,
                            conv.id, request_id, sequence_number,
                            {"tool_name": tool_name, "latency_ms": tool_res.execution_time_ms},
                            user_id
                        )

                # Record trace (Redacting full raw output to keep trace small)
                tools_used.append(tool_name)
                agent_trace.append({
                    "iteration": iteration,
                    "tool": tool_name,
                    "arguments": tool_args,
                    "success": tool_res.success,
                    "latency_ms": round(tool_res.execution_time_ms, 2)
                })
                
                # Append tool result to context for the next LLM turn
                messages.append({"role": "model", "content": json.dumps({"action": "use_tool", "tool_name": tool_name})})
                messages.append({"role": "user", "content": json.dumps({"tool_result": tool_res.data, "error": tool_res.error})})
                
            else:
                agent_trace.append({"error": f"Unknown action: {action}"})
                break
                
    except Exception as e:
        logger.error(f"Error during copilot execution: {e}", exc_info=True)
        sequence_number += 1
        await broadcast_copilot_event(
            WSEventType.COPILOT_REQUEST_FAILED,
            conv.id, request_id, sequence_number,
            {"error": "Internal execution error occurred."},
            user_id
        )
        raise

    # 4. Fallback if loop terminated without final response
    if not final_response_json:
        final_response_json = {
            "executive_summary": "The investigation was aborted due to maximum iteration limits or an internal error.",
            "estimated_risk": 0.0,
            "risk_level": "UNKNOWN",
            "prediction_interval": {"lower": 0.0, "upper": 0.0},
            "confidence": 0.0,
            "contributing_factors": [],
            "retrieved_evidence": [],
            "scenario_results": {},
            "data_quality": 0.0,
            "limitations": "Agent execution terminated early.",
            "disclaimer": "SYNTHETIC DEMONSTRATION DATA. NON-DIAGNOSTIC."
        }

    # Format the final CopilotResponse object
    parsed_response = CopilotResponse(
        answer=final_response_json.get("executive_summary", ""),
        risk_level=final_response_json.get("risk_level", "UNKNOWN"),
        confidence=final_response_json.get("confidence", 0.0),
        disclaimer=final_response_json.get("disclaimer", "SYNTHETIC DEMONSTRATION DATA. NON-DIAGNOSTIC."),
        sources=tools_used,
        agent_trace=agent_trace
    )

    # 5. Save model response
    model_msg = CopilotMessage(
        conversation_id=conv.id,
        role="model",
        content=parsed_response.answer,
        structured_response=parsed_response.model_dump()
    )
    db.add(model_msg)

    # 6. Audit Log
    global_latency = (time.perf_counter() - global_start) * 1000
    await log_copilot_action(
        db=db,
        user_id=user_id,
        action="COPILOT_INVESTIGATION",
        details={
            "query": request.message,
            "iterations": iteration,
            "tools_used": tools_used,
            "latency_ms": global_latency,
            "risk_level": parsed_response.risk_level
        }
    )

    await db.commit()

    sequence_number += 1
    await broadcast_copilot_event(
        WSEventType.COPILOT_REQUEST_COMPLETED,
        conv.id, request_id, sequence_number,
        {"status": "Investigation completed"},
        user_id
    )
    
    return parsed_response

async def get_conversations(db: AsyncSession, user_id: int):
    result = await db.execute(select(CopilotConversation).filter(CopilotConversation.user_id == user_id).order_by(CopilotConversation.updated_at.desc()))
    return result.scalars().all()

async def get_conversation_history(db: AsyncSession, conversation_id: int, user_id: int):
    conv = await db.get(CopilotConversation, conversation_id)
    if not conv or conv.user_id != user_id: raise ValueError("Not found")
    result = await db.execute(select(CopilotMessage).filter(CopilotMessage.conversation_id == conversation_id).order_by(CopilotMessage.created_at.asc()))
    return result.scalars().all()
