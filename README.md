# \# InsiderShield

# 

# \*\*An ML-powered Insider Threat Detection and Investigation Platform\*\*

# 

# InsiderShield is a full-stack security analytics platform designed to detect potentially risky employee activity, identify anomalous behaviour, and support security investigations through explainable alerts and audit history.

# 

# \## Key Features

# 

# \- Event ingestion and validation

# \- Employee-specific Isolation Forest anomaly detection

# \- Rule-based detection with configurable thresholds

# \- Risk scoring using anomaly, severity, frequency, and recency

# \- Explainable security alerts

# \- Investigation management and audit history

# \- JWT authentication, RBAC, and tenant isolation

# 

# \## Tech Stack

# 

# \- Backend: Python, FastAPI, SQLAlchemy

# \- Frontend: React, TypeScript, Vite

# \- Database: PostgreSQL

# \- Background processing: Redis, Celery

# \- Machine Learning: Scikit-learn, Isolation Forest

# \- Infrastructure: Docker, Alembic

# \- Testing: Pytest

# 

# \## Run Locally

# 

# Requirements: Docker Desktop with Docker Compose v2.

# 

# ```powershell

# cd InsiderShield

# Copy-Item .env.example .env

# docker compose up --build -d

# docker compose exec api alembic upgrade head

# docker compose exec api pytest -v

