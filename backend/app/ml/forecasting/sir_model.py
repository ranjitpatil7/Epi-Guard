import numpy as np
from scipy.integrate import odeint
from typing import List, Dict, Any

def _sir_deriv(y, t, N, beta, gamma):
    """
    Differential equations for the SIR model.
    S: Susceptible
    I: Infected
    R: Recovered
    N: Total Population
    beta: Infection rate
    gamma: Recovery rate
    """
    S, I, R = y
    dSdt = -beta * S * I / N
    dIdt = beta * S * I / N - gamma * I
    dRdt = gamma * I
    return dSdt, dIdt, dRdt

def generate_sir_forecast(population: int, initial_infected: int, beta: float, gamma: float, days: int = 30) -> List[Dict[str, Any]]:
    """
    Generates an epidemiological forecast using the SIR mathematical model.
    """
    # Initial conditions
    S0 = population - initial_infected
    I0 = initial_infected
    R0 = 0
    
    # A grid of time points (in days)
    t = np.linspace(0, days, days)
    y0 = S0, I0, R0
    
    # Integrate the SIR equations over the time grid
    ret = odeint(_sir_deriv, y0, t, args=(population, beta, gamma))
    S, I, R = ret.T
    
    forecast = []
    for day in range(days):
        forecast.append({
            "day": int(day),
            "susceptible": int(S[day]),
            "infected": int(I[day]),
            "recovered": int(R[day])
        })
    
    return forecast
