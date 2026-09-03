import pytest
import math
from unittest.mock import AsyncMock, MagicMock
from app.services.logistics_service import haversine
from app.ml.forecasting.sir_model import generate_sir_forecast


class TestSIRMathModel:
    """Tests for the real SIR mathematical model — must not be altered."""

    def test_sir_basic_forecast(self):
        """SIR model produces a valid forecast with correct structure."""
        forecast = generate_sir_forecast(population=50000, initial_infected=10, beta=0.3, gamma=0.1, days=30)
        assert len(forecast) == 30
        for entry in forecast:
            assert "day" in entry
            assert "susceptible" in entry
            assert "infected" in entry
            assert "recovered" in entry

    def test_sir_conservation_of_population(self):
        """S + I + R must equal total population at every timestep."""
        pop = 50000
        forecast = generate_sir_forecast(population=pop, initial_infected=10, beta=0.3, gamma=0.1, days=30)
        for entry in forecast:
            total = entry["susceptible"] + entry["infected"] + entry["recovered"]
            # Allow rounding error of up to 3 due to int() truncation of S, I, and R
            assert abs(total - pop) <= 3, f"Day {entry['day']}: S+I+R={total}, expected {pop}"

    def test_sir_different_populations_produce_different_scales(self):
        """Larger population must produce proportionally larger infection counts."""
        forecast_small = generate_sir_forecast(population=1000, initial_infected=5, beta=0.3, gamma=0.1, days=60)
        forecast_large = generate_sir_forecast(population=500000, initial_infected=5, beta=0.3, gamma=0.1, days=60)
        
        peak_small = max(f["infected"] for f in forecast_small)
        peak_large = max(f["infected"] for f in forecast_large)
        
        assert peak_large > peak_small

    def test_sir_beta_gamma_respected(self):
        """Different beta/gamma values produce different outbreak dynamics."""
        forecast_fast = generate_sir_forecast(population=50000, initial_infected=10, beta=0.8, gamma=0.1, days=30)
        forecast_slow = generate_sir_forecast(population=50000, initial_infected=10, beta=0.15, gamma=0.1, days=30)
        
        peak_day_fast = max(range(30), key=lambda d: forecast_fast[d]["infected"])
        peak_day_slow = max(range(30), key=lambda d: forecast_slow[d]["infected"])
        
        # Higher beta should peak earlier or at similar time with more infections
        peak_infected_fast = forecast_fast[peak_day_fast]["infected"]
        peak_infected_slow = forecast_slow[peak_day_slow]["infected"]
        assert peak_infected_fast > peak_infected_slow


@pytest.mark.asyncio
async def test_sir_endpoint_valid_region():
    """A valid region with population should produce a forecast using that population."""
    from app.api.v1.forecasting import get_sir_forecast
    
    mock_db = AsyncMock()
    mock_region = MagicMock()
    mock_region.id = 1
    mock_region.name = "Test Region"
    mock_region.population = 75000
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_region
    mock_db.execute.return_value = mock_result
    
    response = await get_sir_forecast(
        region_id=1,
        initial_infected=10,
        beta=0.3,
        gamma=0.1,
        days=30,
        db=mock_db
    )
    
    assert response["parameters"]["population"] == 75000
    assert response["parameters"]["population_source"] == "database"
    assert response["region_name"] == "Test Region"
    assert len(response["forecast"]) == 30


@pytest.mark.asyncio
async def test_sir_endpoint_nonexistent_region():
    """A region ID that doesn't exist should return 404."""
    from fastapi import HTTPException
    from app.api.v1.forecasting import get_sir_forecast
    
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await get_sir_forecast(region_id=9999, db=mock_db)
    
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_sir_endpoint_null_population():
    """A region with null population must NOT silently use 100000."""
    from fastapi import HTTPException
    from app.api.v1.forecasting import get_sir_forecast
    
    mock_db = AsyncMock()
    mock_region = MagicMock()
    mock_region.id = 5
    mock_region.name = "Empty Region"
    mock_region.population = None
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_region
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await get_sir_forecast(region_id=5, db=mock_db)
    
    assert exc.value.status_code == 422
    assert "no valid population" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_sir_endpoint_zero_population():
    """A region with population=0 must be rejected."""
    from fastapi import HTTPException
    from app.api.v1.forecasting import get_sir_forecast
    
    mock_db = AsyncMock()
    mock_region = MagicMock()
    mock_region.id = 6
    mock_region.name = "Zero Pop Region"
    mock_region.population = 0
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_region
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await get_sir_forecast(region_id=6, db=mock_db)
    
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_sir_endpoint_uses_different_region_populations():
    """Two different regions must produce forecasts scaled to their actual population."""
    from app.api.v1.forecasting import get_sir_forecast
    
    # Region A: population 10000
    mock_db_a = AsyncMock()
    mock_region_a = MagicMock(id=1, name="Small Village", population=10000)
    mock_result_a = MagicMock()
    mock_result_a.scalar_one_or_none.return_value = mock_region_a
    mock_db_a.execute.return_value = mock_result_a
    
    resp_a = await get_sir_forecast(region_id=1, initial_infected=5, beta=0.3, gamma=0.1, days=60, db=mock_db_a)
    
    # Region B: population 500000
    mock_db_b = AsyncMock()
    mock_region_b = MagicMock(id=2, name="Large City", population=500000)
    mock_result_b = MagicMock()
    mock_result_b.scalar_one_or_none.return_value = mock_region_b
    mock_db_b.execute.return_value = mock_result_b
    
    resp_b = await get_sir_forecast(region_id=2, initial_infected=5, beta=0.3, gamma=0.1, days=60, db=mock_db_b)
    
    peak_a = resp_a["insights"]["peak_infected_count"]
    peak_b = resp_b["insights"]["peak_infected_count"]
    
    assert resp_a["parameters"]["population"] == 10000
    assert resp_b["parameters"]["population"] == 500000
    assert peak_b > peak_a
