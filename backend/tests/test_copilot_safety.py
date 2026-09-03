import pytest
from app.copilot.safety import check_query_safety, SafetyViolation

def test_safety_blocks_diagnostic_query():
    queries = [
        "Do I have cholera?",
        "diagnose me with typhoid",
        "what medication should I take",
        "am I sick",
        "treatment for malaria",
        "cure for dengue"
    ]
    for q in queries:
        with pytest.raises(SafetyViolation) as excinfo:
            check_query_safety(q)
        assert "I cannot diagnose an individual" in str(excinfo.value)

def test_safety_allows_valid_query():
    queries = [
        "Which regions have the highest risk?",
        "Compare Assam and Meghalaya.",
        "What are the current anomalies?",
        "What if rainfall increases in Assam?"
    ]
    for q in queries:
        # Should not raise an exception
        check_query_safety(q)
