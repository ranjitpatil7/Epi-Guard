# EpiGuard AI

**EpiGuard AI is a public-health decision-support and early-warning system, not a medical diagnosis system.**

## Problem Statement
Water-borne diseases significantly impact rural Northeast India, often resulting in delayed detection and response due to geographical and infrastructural challenges. 

## Project Objective
To provide a Smart Community Health Monitoring and Early Warning System for Water-Borne Diseases in Rural Northeast India (SIH25001). This 100% software-only platform combines environmental data, water-quality data, disease trends, community reports, and geographic information to estimate water-borne disease risk, detect anomalies, forecast future risk, and recommend preventive actions to authorized health officials.

## Key Features Planned
- Centralized RBAC for Admins, Health Officials, Analysts, Community Workers, and Users.
- Comprehensive Data Source & Provenance tracking.
- Automated Data Quality Engine and Anomaly Detection.
- Modular AI Models (XGBoost/Random Forest as baseline) with First-Class Model Evaluation tracking.
- Three Operation Modes: Live Data, Demo Data, and Simulation.
- Regional Intelligence module for geospatial analysis and risk ranking.
- AI Decision-Support Copilot (retrieving application data without inventing facts).

## Architecture Overview
Modular Monolith structured into clear service layers:
- **Frontend**: React + Vite + TypeScript, styled with Tailwind CSS & shadcn/ui.
- **Backend**: FastAPI (Python), providing REST APIs, data validation (Pydantic), and ORM (SQLAlchemy 2).
- **Database**: PostgreSQL with PostGIS for spatial data, Redis for caching.

## Local Setup
1. Clone the repository.
2. Ensure Docker and Docker Compose are installed.
3. Copy `.env.example` to `.env` and fill in the secrets.
4. Run `docker compose up -d` to start the database and redis.
5. Setup backend virtual environment and install requirements.
6. Run `alembic upgrade head` to apply database migrations.
7. Setup frontend by running `npm install` and `npm run dev`.

## Environment Variables
See `.env.example` for required configuration variables.

## Development Commands
- **Frontend**: `cd frontend && npm run dev`
- **Backend**: `cd backend && uvicorn app.main:app --reload`
- **Tests**: `pytest` (backend) / `vitest` (frontend)
