import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.risk_fusion_service import RiskFusionService
from app.services.rag_service import RAGService
from app.services.knowledge_graph import KnowledgeGraphService
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline
from app.ml.inference.ensemble_service import ModelEnsembleService
import asyncio

# --- Tool Schemas ---

class ToolResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: float

class RiskAnalystInput(BaseModel):
    region_name: str = Field(..., description="The region to analyze for risk.")

class SpatialAnalystInput(BaseModel):
    region_name: str = Field(..., description="The region to analyze for spatial/neighbor influence.")
    
class ScenarioAnalystInput(BaseModel):
    region_name: str = Field(..., description="The region to simulate.")
    changes: Dict[str, float] = Field(..., description="Key-value pairs of feature changes (e.g., {'rainfall_7d': 50}).")

class EvidenceResearcherInput(BaseModel):
    query: str = Field(..., description="The semantic query to search in the public health knowledge base.")
    region: Optional[str] = Field(None, description="Optional region filter.")

class DataQualityAnalystInput(BaseModel):
    region_name: str = Field(..., description="Region to check data quality metrics.")

class ActiveIncidentsInput(BaseModel):
    region_name: Optional[str] = Field(None, description="Optional region filter.")

class IncidentDetailsInput(BaseModel):
    incident_id: str = Field(..., description="The ID of the incident to fetch.")

class InvestigateIncidentInput(BaseModel):
    incident_id: str = Field(..., description="The ID of the incident to investigate.")

class RiskHistoryInput(BaseModel):
    region_name: str = Field(..., description="The region to get risk history for.")
    
class LatestRiskSnapshotInput(BaseModel):
    region_name: str = Field(..., description="The region to get the latest risk snapshot for.")

class AlertDetailsInput(BaseModel):
    alert_id: int = Field(..., description="The ID of the alert to fetch.")

class RiskLineageInput(BaseModel):
    snapshot_id: str = Field(..., description="The snapshot ID to get lineage for.")

# --- Tool Registry (Governance) ---
# Enforces timeouts and explicit allowlisting

from app.models.users import User, UserStatus
from app.core.permissions import Permission, get_permissions_for_role
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, db: AsyncSession, user: User = None):
        self.db = db
        self.user = user
        self.tools = {
            "risk_analyst": {"func": self.risk_analyst, "input": RiskAnalystInput, "timeout": 2.0, "required_permission": Permission.VIEW_RISK, "region_arg": "region_name"},
            "spatial_analyst": {"func": self.spatial_analyst, "input": SpatialAnalystInput, "timeout": 2.0, "required_permission": Permission.VIEW_MAP, "region_arg": "region_name"},
            "scenario_analyst": {"func": self.scenario_analyst, "input": ScenarioAnalystInput, "timeout": 5.0, "required_permission": Permission.RUN_SIMULATION, "region_arg": "region_name"},
            "evidence_researcher": {"func": self.evidence_researcher, "input": EvidenceResearcherInput, "timeout": 3.0, "required_permission": Permission.VIEW_COMMUNITY_REPORTS, "region_arg": "region"},
            "data_quality_analyst": {"func": self.data_quality_analyst, "input": DataQualityAnalystInput, "timeout": 1.0, "required_permission": Permission.VIEW_DATA_QUALITY, "region_arg": "region_name"},
            "get_active_incidents": {"func": self.get_active_incidents, "input": ActiveIncidentsInput, "timeout": 2.0, "required_permission": Permission.VIEW_ALERTS, "region_arg": "region_name"},
            "get_incident_details": {"func": self.get_incident_details, "input": IncidentDetailsInput, "timeout": 2.0, "required_permission": Permission.VIEW_ALERTS, "id_based": "incident_id"},
            "investigate_incident": {"func": self.investigate_incident, "input": InvestigateIncidentInput, "timeout": 5.0, "required_permission": Permission.VIEW_ALERTS, "id_based": "incident_id"},
            "get_risk_history": {"func": self.get_risk_history, "input": RiskHistoryInput, "timeout": 3.0, "required_permission": Permission.VIEW_RISK, "region_arg": "region_name"},
            "get_latest_risk_snapshot": {"func": self.get_latest_risk_snapshot, "input": LatestRiskSnapshotInput, "timeout": 2.0, "required_permission": Permission.VIEW_RISK, "region_arg": "region_name"},
            "get_alert_details": {"func": self.get_alert_details, "input": AlertDetailsInput, "timeout": 2.0, "required_permission": Permission.VIEW_ALERTS, "id_based": "alert_id"},
            "get_risk_lineage": {"func": self.get_risk_lineage, "input": RiskLineageInput, "timeout": 3.0, "required_permission": Permission.VIEW_MODEL_INTELLIGENCE, "id_based": "snapshot_id"}
        }

    async def _check_region_authorization(self, tool_def: Dict[str, Any], arguments: Dict[str, Any]) -> bool:
        """Returns True if authorized or no restriction, False if region access denied."""
        if not self.user or self.user.region_id is None:
            return True # National scope user has access to all regions
            
        target_region_id = None
        
        # 1. Direct region_name string argument
        if "region_arg" in tool_def and arguments.get(tool_def["region_arg"]):
            region_name = arguments[tool_def["region_arg"]]
            target_region_id = await self._get_region_id(region_name)
            
        # 2. Resource ID-based argument requiring DB lookup
        elif "id_based" in tool_def and arguments.get(tool_def["id_based"]):
            id_key = tool_def["id_based"]
            val = arguments[id_key]
            from sqlalchemy import select
            
            if id_key == "incident_id":
                from app.models.domain import IntelligenceIncident
                res = await self.db.execute(select(IntelligenceIncident.region_id).where(IntelligenceIncident.incident_id == val))
                target_region_id = res.scalar_one_or_none()
            elif id_key == "alert_id":
                from app.models.domain import Alert
                res = await self.db.execute(select(Alert.region_id).where(Alert.id == int(val)))
                target_region_id = res.scalar_one_or_none()
            elif id_key == "snapshot_id":
                from app.models.domain import RiskSnapshot
                res = await self.db.execute(select(RiskSnapshot.region_id).where(RiskSnapshot.snapshot_id == val))
                target_region_id = res.scalar_one_or_none()
                
        # If a region is targeted and it does not match the user's restricted region, deny
        if target_region_id is not None and target_region_id != self.user.region_id:
            return False
            
        return True
        
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResponse:
        start_time = time.perf_counter()
        
        # DEFAULT DENY
        if name not in self.tools:
            logger.warning(f"AUTH DENY: Tool {name} not found or not allowlisted.")
            return ToolResponse(success=False, data={}, error="Tool execution denied: You are not authorized to access this information.", execution_time_ms=0)
            
        tool = self.tools[name]
        
        # 1. Check User Authenticated and Active
        if not self.user or self.user.status != UserStatus.ACTIVE:
            logger.warning(f"AUTH DENY: Unauthenticated or inactive user attempting to run {name}.")
            return ToolResponse(success=False, data={}, error="Tool execution denied: You are not authorized to access this information.", execution_time_ms=0)
            
        # 2. Check Permission (Default Deny if no required_permission defined)
        required_perm = tool.get("required_permission")
        if not required_perm or required_perm not in get_permissions_for_role(self.user.role):
            logger.warning(f"AUTH DENY: User {self.user.username} lacks {required_perm} for tool {name}.")
            return ToolResponse(success=False, data={}, error="Tool execution denied: You are not authorized to access this information.", execution_time_ms=0)
            
        # 3. Check Region Authorization (Direct and ID-based)
        is_region_authorized = await self._check_region_authorization(tool, arguments)
        if not is_region_authorized:
            logger.warning(f"AUTH DENY: User {self.user.username} (Region: {self.user.region_id}) denied access to resource in another region via {name}.")
            return ToolResponse(success=False, data={}, error="Tool execution denied: You are not authorized to access this information.", execution_time_ms=0)
            
        try:
            # Validate input schema
            validated_input = tool["input"](**arguments)
            
            # Execute with timeout
            result = await asyncio.wait_for(tool["func"](validated_input), timeout=tool["timeout"])
            
            # RAG Prompt Injection Defense: Sanitize outputs if returning evidence
            if name == "evidence_researcher":
                result = self._sanitize_evidence(result)
                
            execution_time = (time.perf_counter() - start_time) * 1000
            return ToolResponse(success=True, data=result, execution_time_ms=execution_time)
            
        except asyncio.TimeoutError:
            return ToolResponse(success=False, data={}, error=f"Tool {name} timed out.", execution_time_ms=(time.perf_counter() - start_time)*1000)
        except Exception as e:
            return ToolResponse(success=False, data={}, error="An internal execution error occurred.", execution_time_ms=(time.perf_counter() - start_time)*1000)

    def _sanitize_evidence(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Prevents RAG chunks from hijacking the LLM prompt."""
        if "evidence" in result:
            for ev in result["evidence"]:
                # Strip out common prompt injection markers
                text = ev.get("excerpt", "")
                text = text.replace("Ignore previous instructions", "[REDACTED]")
                text = text.replace("System prompt", "[REDACTED]")
                text = text.replace("You are now", "[REDACTED]")
                ev["excerpt"] = text
        return result

    # --- Tool Implementations ---
    
    async def _get_region_id(self, name: str) -> Optional[int]:
        from sqlalchemy import text
        # Real DB lookup (case-insensitive fuzzy match)
        query = text("SELECT id FROM regions WHERE LOWER(name) LIKE LOWER(:name) LIMIT 1")
        result = await self.db.execute(query, {"name": f"%{name}%"})
        row = result.fetchone()
        if row:
            return row.id
        return None

    async def risk_analyst(self, args: RiskAnalystInput) -> Dict[str, Any]:
        region_id = await self._get_region_id(args.region_name)
        if not region_id: raise ValueError(f"Region '{args.region_name}' not found in database.")
        from datetime import datetime, timezone
        result = await RiskFusionService.get_fused_risk(self.db, region_id, datetime.now(timezone.utc))
        return result

    async def spatial_analyst(self, args: SpatialAnalystInput) -> Dict[str, Any]:
        graph = await KnowledgeGraphService.get_region_neighbors(self.db, args.region_name)
        return graph

    async def scenario_analyst(self, args: ScenarioAnalystInput) -> Dict[str, Any]:
        region_id = await self._get_region_id(args.region_name)
        if not region_id: raise ValueError(f"Region '{args.region_name}' not found in database.")
        from datetime import datetime, timezone
        
        # 1. Baseline
        baseline = await RiskFusionService.get_fused_risk(self.db, region_id, datetime.now(timezone.utc))
        
        # 2. Modify features
        modified_features = baseline["features_used"].copy()
        for k, v in args.changes.items():
            if isinstance(v, (int, float)):
                if k.endswith("_percentage"):
                    modified_features[k.replace("_percentage", "")] *= (1.0 + (v / 100.0))
                else:
                    modified_features[k] += v
                    
        # 3. Predict Scenario
        ensemble_result = ModelEnsembleService.evaluate_ensemble(modified_features)
        
        # 4. Compare
        baseline_score = baseline["estimated_risk_score"]
        scenario_score = ensemble_result["ensemble"]
        change = scenario_score - baseline_score
        
        return {
            "baseline_risk": baseline_score,
            "scenario_risk": scenario_score,
            "absolute_change": round(change, 2),
            "percentage_change": round((change / max(1, baseline_score)) * 100, 2) if baseline_score else 0.0,
            "changed_factors": args.changes,
            "warning": "SCENARIO ANALYSIS — NOT CAUSAL PROOF. Represents statistical correlation from historical simulated data."
        }

    async def evidence_researcher(self, args: EvidenceResearcherInput) -> Dict[str, Any]:
        filters = {"region": args.region} if args.region else None
        evidence = await RAGService.retrieve_evidence(self.db, args.query, filters=filters)
        return {"evidence": evidence}

    async def data_quality_analyst(self, args: DataQualityAnalystInput) -> Dict[str, Any]:
        region_id = await self._get_region_id(args.region_name)
        if not region_id: raise ValueError(f"Region '{args.region_name}' not found in database.")
        from datetime import datetime, timezone
        result = await RiskFusionService.get_fused_risk(self.db, region_id, datetime.now(timezone.utc))
        return {"data_quality_score": result.get("data_quality_score", 1.0), "limitations": result.get("uncertainty_explanation", "None")}

    async def get_active_incidents(self, args: ActiveIncidentsInput) -> Dict[str, Any]:
        from app.models.domain import IntelligenceIncident
        from sqlalchemy import select, and_
        stmt = select(IntelligenceIncident).where(IntelligenceIncident.status.in_(["OPEN", "INVESTIGATING", "ESCALATED"]))
        if args.region_name:
            region_id = await self._get_region_id(args.region_name)
            if region_id:
                stmt = stmt.where(IntelligenceIncident.region_id == region_id)
        result = await self.db.execute(stmt)
        incidents = result.scalars().all()
        return {
            "incidents": [
                {
                    "incident_id": inc.incident_id,
                    "type": inc.incident_type,
                    "severity": inc.severity.value if hasattr(inc.severity, "value") else inc.severity,
                    "status": inc.status.value if hasattr(inc.status, "value") else inc.status,
                    "region_id": inc.region_id
                } for inc in incidents
            ]
        }

    async def get_incident_details(self, args: IncidentDetailsInput) -> Dict[str, Any]:
        from app.models.domain import IntelligenceIncident
        from sqlalchemy import select
        stmt = select(IntelligenceIncident).where(IntelligenceIncident.incident_id == args.incident_id)
        result = await self.db.execute(stmt)
        inc = result.scalar_one_or_none()
        if not inc:
            return {"error": "Incident not found"}
            
        return {
            "incident_id": inc.incident_id,
            "type": inc.incident_type,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity.value if hasattr(inc.severity, "value") else inc.severity,
            "confidence": inc.confidence,
            "status": inc.status.value if hasattr(inc.status, "value") else inc.status,
            "events": inc.source_event_ids,
            "rules": inc.triggered_rules,
            "evidence": inc.evidence,
            "spatial_context": inc.spatial_context,
            "temporal_context": inc.temporal_context
        }

    async def investigate_incident(self, args: InvestigateIncidentInput) -> Dict[str, Any]:
        """Provides an aggregated knowledge graph view of an incident's context."""
        details = await self.get_incident_details(IncidentDetailsInput(incident_id=args.incident_id))
        if "error" in details:
            return details
            
        # Get spatial context
        neighbors = []
        if details.get("region_id"):
            from app.models.domain import Region
            from sqlalchemy import select
            reg_res = await self.db.execute(select(Region.name).where(Region.id == details["region_id"]))
            reg_name = reg_res.scalar_one_or_none()
            if reg_name:
                neighbors_graph = await KnowledgeGraphService.get_region_neighbors(self.db, reg_name)
                neighbors = neighbors_graph.get("edges", [])
                
        return {
            "incident": details,
            "spatial_propagation_risk": neighbors,
            "warning": "Incidents represent regional environmental/risk correlations, NOT medical diagnoses."
        }
        
    async def get_risk_history(self, args: RiskHistoryInput) -> Dict[str, Any]:
        region_id = await self._get_region_id(args.region_name)
        if not region_id: raise ValueError("Region not found")
        from sqlalchemy import select
        from app.models.domain import RiskSnapshot
        stmt = select(RiskSnapshot).where(RiskSnapshot.region_id == region_id).order_by(RiskSnapshot.timestamp.desc()).limit(10)
        result = await self.db.execute(stmt)
        snapshots = result.scalars().all()
        return {
            "history": [
                {
                    "snapshot_id": s.snapshot_id,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    "current_risk": s.current_risk,
                    "risk_delta": s.risk_delta
                } for s in snapshots
            ]
        }
        
    async def get_latest_risk_snapshot(self, args: LatestRiskSnapshotInput) -> Dict[str, Any]:
        region_id = await self._get_region_id(args.region_name)
        if not region_id: raise ValueError("Region not found")
        from sqlalchemy import select
        from app.models.domain import RiskSnapshot
        stmt = select(RiskSnapshot).where(RiskSnapshot.region_id == region_id).order_by(RiskSnapshot.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        s = result.scalar_one_or_none()
        if not s: return {"error": "No snapshot found"}
        return {
            "snapshot_id": s.snapshot_id,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "current_risk": s.current_risk,
            "confidence": s.confidence,
            "explanation": s.explanation_metadata,
            "features": s.feature_snapshot
        }
        
    async def get_alert_details(self, args: AlertDetailsInput) -> Dict[str, Any]:
        from sqlalchemy import select
        from app.models.domain import Alert
        stmt = select(Alert).where(Alert.id == args.alert_id)
        result = await self.db.execute(stmt)
        a = result.scalar_one_or_none()
        if not a: return {"error": "Alert not found"}
        return {
            "id": a.id,
            "severity": a.severity,
            "message": a.message,
            "is_active": a.is_active,
            "confidence": a.confidence,
            "prediction_interval": a.prediction_interval,
            "risk_snapshot_id": a.risk_snapshot_id
        }
        
    async def get_risk_lineage(self, args: RiskLineageInput) -> Dict[str, Any]:
        from app.services.risk_lineage_service import RiskLineageService
        lineage = await RiskLineageService.get_snapshot_lineage(self.db, args.snapshot_id)
        if not lineage: return {"error": "Lineage not found"}
        return {"lineage": lineage}
