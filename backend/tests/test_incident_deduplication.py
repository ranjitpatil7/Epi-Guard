import pytest
from app.cep.deduplication import IncidentDeduplicator
from datetime import datetime, timezone, timedelta

def test_time_bucket():
    dt = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
    # 6 hour bucket
    # 14:30 should fall into the 12:00 bucket which is bucket index 2
    bucket = IncidentDeduplicator.get_time_bucket(dt, 6)
    assert bucket == "2026-08-11_2"
    
    dt2 = datetime(2026, 8, 11, 19, 59, tzinfo=timezone.utc)
    bucket2 = IncidentDeduplicator.get_time_bucket(dt2, 6)
    assert bucket2 == "2026-08-11_3"

def test_generate_fingerprint():
    bucket = "2026-08-11T12:00"
    fp1 = IncidentDeduplicator.generate_fingerprint("COMPOUND_RISK_EVENT", 1, bucket)
    fp2 = IncidentDeduplicator.generate_fingerprint("COMPOUND_RISK_EVENT", 1, bucket)
    fp3 = IncidentDeduplicator.generate_fingerprint("COMPOUND_RISK_EVENT", 2, bucket)
    
    assert fp1 == fp2
    assert fp1 != fp3
