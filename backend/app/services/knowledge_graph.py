from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.domain import Region, RiskAssessment, Alert, Anomaly, CommunityReport, EnvironmentalData
from app.models.knowledge import KnowledgeDocument
from app.services.rag_service import RAGService

class KnowledgeGraphService:
    """
    Simulates Knowledge Graph traversal over the relational PostGIS database.
    Provides structured graph-like objects (Nodes and Edges).
    """

    @staticmethod
    async def get_region_neighbors(db: AsyncSession, region_name: str, distance_km: float = 100.0) -> Dict[str, Any]:
        """Region -> Neighbor Region (Spatial Edge)"""
        query = text(f"""
            SELECT n.name, n.state, n.population,
                   ST_Distance(r.geom::geography, n.geom::geography) / 1000.0 as distance_km
            FROM regions r
            JOIN regions n ON ST_DWithin(r.geom::geography, n.geom::geography, :dist * 1000)
            WHERE r.name = :name AND r.id != n.id
            ORDER BY distance_km ASC
        """)
        
        result = await db.execute(query, {"name": region_name, "dist": distance_km})
        neighbors = []
        for row in result.all():
            neighbors.append({
                "node_type": "Region",
                "name": row.name,
                "state": row.state,
                "population": row.population,
                "edge_type": "NEIGHBORS",
                "edge_properties": {"distance_km": round(row.distance_km, 2)}
            })
            
        return {
            "source_node": {"type": "Region", "name": region_name},
            "edges": neighbors
        }

    @staticmethod
    async def get_region_risk_context(db: AsyncSession, region_name: str) -> Dict[str, Any]:
        """Region -> Risk Assessment & Environmental Factor"""
        region_res = await db.execute(select(Region).where(Region.name == region_name))
        region = region_res.scalar_one_or_none()
        
        if not region:
            return {"error": "Region not found"}
            
        # Get latest risk
        risk_res = await db.execute(select(RiskAssessment).where(RiskAssessment.region_id == region.id).order_by(RiskAssessment.target_date.desc()).limit(1))
        risk = risk_res.scalar_one_or_none()
        
        # Get latest environmental data
        env_res = await db.execute(select(EnvironmentalData).where(EnvironmentalData.region_id == region.id).order_by(EnvironmentalData.date.desc()).limit(1))
        env = env_res.scalar_one_or_none()
        
        edges = []
        if risk:
            edges.append({
                "node_type": "RiskAssessment",
                "id": risk.id,
                "edge_type": "HAS_RISK",
                "properties": {"score": risk.estimated_risk_score, "level": risk.risk_level, "date": str(risk.target_date)}
            })
            
        if env:
            edges.append({
                "node_type": "EnvironmentalFactor",
                "id": env.id,
                "edge_type": "HAS_ENVIRONMENT",
                "properties": {"rainfall": env.rainfall, "temperature": env.temperature, "water_quality_index": env.water_quality_index}
            })
            
        return {
            "source_node": {"type": "Region", "name": region_name},
            "edges": edges
        }

    @staticmethod
    async def get_region_alerts(db: AsyncSession, region_name: str) -> Dict[str, Any]:
        """Region -> Alert & Anomaly"""
        region_res = await db.execute(select(Region).where(Region.name == region_name))
        region = region_res.scalar_one_or_none()
        
        if not region:
            return {"error": "Region not found"}
            
        alerts_res = await db.execute(select(Alert).where(Alert.region_id == region.id).order_by(Alert.created_at.desc()).limit(5))
        alerts = alerts_res.scalars().all()
        
        anomalies_res = await db.execute(select(Anomaly).where(Anomaly.region_id == region.id).order_by(Anomaly.detected_at.desc()).limit(5))
        anomalies = anomalies_res.scalars().all()
        
        edges = []
        for a in alerts:
            edges.append({
                "node_type": "Alert",
                "id": a.id,
                "edge_type": "HAS_ALERT",
                "properties": {"severity": a.severity, "message": a.message}
            })
            
        for an in anomalies:
            edges.append({
                "node_type": "Anomaly",
                "id": an.id,
                "edge_type": "HAS_ANOMALY",
                "properties": {"feature": an.feature_name, "score": an.anomaly_score}
            })
            
        return {
            "source_node": {"type": "Region", "name": region_name},
            "edges": edges
        }

    @staticmethod
    async def get_region_incidents(db: AsyncSession, region_name: str) -> Dict[str, Any]:
        """Region -> IntelligenceIncident"""
        from app.models.domain import IntelligenceIncident
        
        region_res = await db.execute(select(Region).where(Region.name == region_name))
        region = region_res.scalar_one_or_none()
        
        if not region:
            return {"error": "Region not found"}
            
        incidents_res = await db.execute(
            select(IntelligenceIncident)
            .where(IntelligenceIncident.region_id == region.id)
            .order_by(IntelligenceIncident.first_detected_at.desc())
            .limit(5)
        )
        incidents = incidents_res.scalars().all()
        
        edges = []
        for inc in incidents:
            edges.append({
                "node_type": "IntelligenceIncident",
                "id": inc.incident_id,
                "edge_type": "CORRELATED_WITH",
                "properties": {
                    "type": inc.incident_type, 
                    "severity": inc.severity.value if hasattr(inc.severity, "value") else inc.severity,
                    "status": inc.status.value if hasattr(inc.status, "value") else inc.status
                }
            })
            
        return {
            "source_node": {"type": "Region", "name": region_name},
            "edges": edges
        }

    @staticmethod
    async def get_related_evidence(db: AsyncSession, risk_factor: str) -> Dict[str, Any]:
        """Risk Factor -> Evidence Document"""
        # Semantic search against the risk factor
        evidence = await RAGService.retrieve_evidence(db, query=risk_factor, top_k=3, similarity_threshold=0.4)
        
        edges = []
        for doc in evidence:
            edges.append({
                "node_type": "Document",
                "id": doc["document_id"],
                "title": doc["title"],
                "edge_type": "EVIDENCE_FOR",
                "properties": {"similarity": doc["similarity_score"], "excerpt": doc["excerpt"]}
            })
            
        return {
            "source_node": {"type": "RiskFactor", "name": risk_factor},
            "edges": edges
        }

    @staticmethod
    async def get_document_topics(db: AsyncSession, document_id: int) -> Dict[str, Any]:
        """Document -> Topic"""
        doc_res = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id))
        doc = doc_res.scalar_one_or_none()
        
        if not doc:
            return {"error": "Document not found"}
            
        return {
            "source_node": {"type": "Document", "id": doc.id, "title": doc.title},
            "edges": [{
                "node_type": "Topic",
                "name": doc.topic,
                "edge_type": "ABOUT_TOPIC"
            }]
        }
