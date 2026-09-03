import pytest
from app.models.domain import IntelligenceIncident, IncidentStatus, IncidentSeverity
import uuid

def test_event_lineage_fields():
    # Verify that the model supports arrays and JSON fields for lineage tracking
    inc = IntelligenceIncident(
        incident_id=str(uuid.uuid4()),
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.MEDIUM,
        source_event_ids=["e1", "e2"],
        triggered_rules=["RULE_1", "RULE_2"],
        evidence={"risk_delta": 0.5},
        spatial_context={"radius": 10},
        temporal_context={"window": "5m"}
    )
    
    assert "e1" in inc.source_event_ids
    assert "RULE_2" in inc.triggered_rules
    assert inc.evidence["risk_delta"] == 0.5
