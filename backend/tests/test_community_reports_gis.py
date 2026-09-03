import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.users import UserRole
from app.models.domain import CommunityReport, Region
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import TestingSessionLocal
from sqlalchemy import text

@pytest_asyncio.fixture
async def gis_data_setup(db_setup):
    # Insert test data using raw SQL to ensure PostGIS ST_GeomFromText is used
    async with TestingSessionLocal() as session:
        # Create 2 regions
        await session.execute(text("""
            INSERT INTO regions (id, name, geometry) 
            VALUES (101, 'Test Region A', ST_GeomFromText('POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))', 4326))
            ON CONFLICT DO NOTHING
        """))
        await session.execute(text("""
            INSERT INTO regions (id, name, geometry) 
            VALUES (102, 'Test Region B', ST_GeomFromText('POLYGON((20 20, 20 30, 30 30, 30 20, 20 20))', 4326))
            ON CONFLICT DO NOTHING
        """))
        
        # Create reports
        # Report 1 inside Region A (5, 5)
        await session.execute(text("""
            INSERT INTO community_reports (id, text_content, location)
            VALUES (1001, 'Report inside A', ST_GeomFromText('POINT(5 5)', 4326))
            ON CONFLICT DO NOTHING
        """))
        # Report 2 inside Region B (25, 25)
        await session.execute(text("""
            INSERT INTO community_reports (id, text_content, location)
            VALUES (1002, 'Report inside B', ST_GeomFromText('POINT(25 25)', 4326))
            ON CONFLICT DO NOTHING
        """))
        # Report 3 outside both (50, 50)
        await session.execute(text("""
            INSERT INTO community_reports (id, text_content, location)
            VALUES (1003, 'Report outside', ST_GeomFromText('POINT(50 50)', 4326))
            ON CONFLICT DO NOTHING
        """))
        # Report 4 null location
        await session.execute(text("""
            INSERT INTO community_reports (id, text_content, location)
            VALUES (1004, 'Report null', NULL)
            ON CONFLICT DO NOTHING
        """))
        await session.commit()
    
    yield
    
    # Teardown
    async with TestingSessionLocal() as session:
        await session.execute(text("DELETE FROM community_reports WHERE id IN (1001, 1002, 1003, 1004)"))
        await session.execute(text("UPDATE users SET region_id = NULL WHERE region_id IN (101, 102)"))
        await session.execute(text("DELETE FROM regions WHERE id IN (101, 102)"))
        await session.commit()


@pytest.mark.asyncio
async def test_gis_region_filtering_global_user(auth_client_factory, async_client: AsyncClient, gis_data_setup):
    """1. A report inside Region A is returned for Region A, 2. B is NOT returned for A."""
    await auth_client_factory(UserRole.ADMINISTRATOR) # Global user
    
    # Query Region 101
    res = await async_client.get("/api/v1/community-reports/?region_id=101")
    assert res.status_code == 200
    data = res.json()["data"]
    
    # Should only contain Report 1
    report_texts = [r["text"] for r in data]
    assert "Report inside A" in report_texts
    assert "Report inside B" not in report_texts
    assert "Report outside" not in report_texts
    assert "Report null" not in report_texts
    
@pytest.mark.asyncio
async def test_gis_region_filtering_invalid_region(auth_client_factory, async_client: AsyncClient, gis_data_setup):
    """4. Invalid/nonexistent region IDs are handled correctly."""
    await auth_client_factory(UserRole.ADMINISTRATOR)
    
    res = await async_client.get("/api/v1/community-reports/?region_id=999999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Region not found"

@pytest.mark.asyncio
async def test_gis_null_locations_do_not_crash(auth_client_factory, async_client: AsyncClient, gis_data_setup):
    """5. Reports with null/missing locations do not crash the query."""
    await auth_client_factory(UserRole.ADMINISTRATOR)
    
    # Without region filter, null should be returned
    res = await async_client.get("/api/v1/community-reports/")
    assert res.status_code == 200
    data = res.json()["data"]
    report_texts = [r["text"] for r in data]
    
    assert "Report null" in report_texts
    
    # With region filter, null should NOT match
    res_filtered = await async_client.get("/api/v1/community-reports/?region_id=101")
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.json()["data"]
    report_texts_filtered = [r["text"] for r in data_filtered]
    
    assert "Report null" not in report_texts_filtered

@pytest.mark.asyncio
async def test_region_scoped_user_cannot_query_unauthorized_region(auth_client_factory, async_client: AsyncClient, gis_data_setup):
    """7. Region-scoped users cannot query another unauthorized region."""
    # We can't trivially set region_id in the auth_client_factory, but we can update the user directly.
    await auth_client_factory(UserRole.FIELD_OFFICER)
    
    from sqlalchemy import update
    from app.models.users import User
    
    async with TestingSessionLocal() as session:
        # Give current user region 101
        me_res = await async_client.get("/api/v1/auth/me")
        user_id = me_res.json()["id"]
        
        await session.execute(update(User).where(User.id == user_id).values(region_id=101))
        await session.commit()
        
    # Attempting to query Region 102 should fail (403)
    res_unauthorized = await async_client.get("/api/v1/community-reports/?region_id=102")
    assert res_unauthorized.status_code == 403
    
    # Attempting to query Region 101 should succeed (200)
    res_authorized = await async_client.get("/api/v1/community-reports/?region_id=101")
    assert res_authorized.status_code == 200
    report_texts = [r["text"] for r in res_authorized.json()["data"]]
    assert "Report inside A" in report_texts
    
    # Attempting to query globally (region_id omitted) should implicitly restrict to Region 101
    res_implicit = await async_client.get("/api/v1/community-reports/")
    assert res_implicit.status_code == 200
    report_texts_implicit = [r["text"] for r in res_implicit.json()["data"]]
    assert "Report inside A" in report_texts_implicit
    assert "Report inside B" not in report_texts_implicit
