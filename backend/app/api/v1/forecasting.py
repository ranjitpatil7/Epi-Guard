from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.ml.forecasting.sir_model import generate_sir_forecast
from app.db.session import get_db
from app.models.domain import Region

router = APIRouter()

@router.get("/sir/{region_id}", response_model=Dict[str, Any])
async def get_sir_forecast(
    region_id: int,
    initial_infected: int = Query(50, description="Current number of infected individuals (simulation parameter)"),
    beta: float = Query(0.3, description="Effective contact rate (transmission rate)"),
    gamma: float = Query(0.1, description="Recovery rate (1/days to recover)"),
    days: int = Query(30, description="Number of days to forecast"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Generate an epidemiological SIR forecast for a given region.
    
    Population is sourced from the Region database record (Region.population).
    initial_infected is a configurable simulation parameter (no real-time
    epidemiological case count exists in the current data model).
    beta and gamma are user-configurable transmission/recovery rates.
    """
    # 1. Fetch the real Region from the database
    stmt = select(Region).where(Region.id == region_id)
    result = await db.execute(stmt)
    region = result.scalar_one_or_none()
    
    if region is None:
        raise HTTPException(status_code=404, detail=f"Region with ID {region_id} not found.")
    
    # 2. Use the real database population — never silently fall back to a default
    population = region.population
    if population is None or population <= 0:
        raise HTTPException(
            status_code=422,
            detail=f"Region '{region.name}' (ID {region_id}) has no valid population data (value: {population}). "
                   f"Cannot run SIR forecast without a real population count."
        )
    
    # 3. Validate simulation parameters
    if initial_infected < 0 or days <= 0:
        raise HTTPException(status_code=400, detail="Invalid parameters for SIR model.")
    
    if initial_infected >= population:
        raise HTTPException(
            status_code=400,
            detail=f"initial_infected ({initial_infected}) must be less than the region population ({population})."
        )
        
    try:
        forecast_data = generate_sir_forecast(
            population=population,
            initial_infected=initial_infected,
            beta=beta,
            gamma=gamma,
            days=days
        )
        
        # Calculate Peak Infection Day
        peak_infection = max(forecast_data, key=lambda x: x["infected"])
        
        return {
            "region_id": region_id,
            "region_name": region.name,
            "parameters": {
                "population": population,
                "population_source": "database",
                "initial_infected": initial_infected,
                "initial_infected_source": "simulation_parameter",
                "beta": beta,
                "gamma": gamma,
                "days": days,
                "R0": round(beta / gamma, 2) if gamma > 0 else 0
            },
            "insights": {
                "peak_infection_day": peak_infection["day"],
                "peak_infected_count": peak_infection["infected"],
                "herd_immunity_threshold": f"{round((1 - (gamma / beta)) * 100, 1)}%" if beta > gamma else "N/A"
            },
            "forecast": forecast_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
