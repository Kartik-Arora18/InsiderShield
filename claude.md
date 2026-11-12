
# InsiderShield — Master Project Instructions

## 1. Project Vision

Build InsiderShield from scratch: a professional, AI-powered Insider Threat Detection Platform for organisations.

The platform should help security teams detect suspicious employee activity, identify behavioural anomalies, calculate explainable risk scores, and investigate potential insider threats.

This must be a complete, functional, portfolio-quality software engineering and AI/ML project.

Do not create a superficial demo or a static dashboard.

## 2. Core Technology Stack

Frontend:
- Next.js with App Router
- TypeScript
- Tailwind CSS
- Responsive UI
- Professional cybersecurity dashboard

Backend:
- Python
- FastAPI
- Pydantic
- SQLAlchemy

Database:
- PostgreSQL
- Redis for caching and background processing

Background processing:
- Celery

AI and Machine Learning:
- Scikit-learn
- Isolation Forest for anomaly detection
- Behavioural baselines
- Explainable risk scoring
- Model evaluation and versioning

Authentication:
- JWT
- Role-based access control
- Secure password hashing

Infrastructure:
- Docker
- Docker Compose
- GitHub Actions

Testing:
- Pytest
- Playwright
- API integration tests

## 3. Main Product Modules

Build these modules:

1. Authentication and organisation management.
2. Employee management and user roles.
3. Activity and event ingestion APIs.
4. Employee behavioural analytics.
5. Anomaly detection engine.
6. Explainable insider risk scoring.
7. Security alerts and investigation workflows.
8. Investigation history and audit logs.
9. Analytics dashboard and reporting.
10. API documentation and health monitoring.

## 4. Activity Event Types

Initially use synthetic, clearly labelled employee activity data.

Support events such as:
- Login and logout
- Failed authentication
- Unusual login time
- File access
- Bulk file downloads
- Permission changes
- Unusual data transfers
- Access to sensitive resources
- Privilege escalation attempts

Do not collect private communications or monitor personal devices.
Use authorised, consent-based and organisation-approved data sources only.

## 5. AI/ML Requirements

Build an actual machine learning pipeline.

It should:
- Process employee activity events.
- Establish behavioural baselines.
- Detect unusual behaviour.
- Calculate risk scores.
- Explain why an activity was flagged.
- Track model performance.
- Support reproducible training and evaluation.

Do not pretend that a rule-based score is a trained AI model.
Clearly distinguish ML predictions from deterministic security rules.

## 6. Security Requirements

Implement:
- Secure authentication
- Password hashing
- JWT validation
- Organisation-level data isolation
- Role-based permissions
- Input validation
- Rate limiting
- Secure secrets management
- Audit logging
- Safe error handling
- Database migrations

Never hardcode secrets or commit API keys.

## 7. Engineering Standards

- Use modular and maintainable architecture.
- Follow clean code principles.
- Use type hints.
- Add meaningful documentation.
- Write automated tests.
- Avoid unnecessary dependencies.
- Never leave fake implementations presented as complete features.
- Never silently ignore errors.
- Keep frontend and backend contracts consistent.

## 8. Development Strategy

Work in milestones:

Milestone 1: Architecture and project foundation.
Milestone 2: Database, authentication and organisation management.
Milestone 3: Activity ingestion and event processing.
Milestone 4: AI/ML anomaly detection and risk scoring.
Milestone 5: Frontend security dashboard.
Milestone 6: Alerts and investigation workflows.
Milestone 7: Integration, testing and hardening.
Milestone 8: Docker deployment, documentation and CI/CD.

## 9. How You Must Work

Act as a senior software architect and full-stack engineering agent.

Before implementing:
1. Inspect the existing repository.
2. Propose the architecture.
3. Identify dependencies.
4. Create a detailed implementation roadmap.
5. Identify security and technical risks.

After approval:
- Implement one milestone at a time.
- Create real working code.
- Run tests after each milestone.
- Fix failures before proceeding.
- Update documentation.
- Maintain a progress checklist.

Do not overwrite existing files without inspecting them.
Do not execute destructive commands without approval.
Do not deploy anything without explicit approval.

## 10. Final Quality Goal

The finished project should demonstrate:
- Strong software engineering
- Real backend architecture
- Real database design
- Working REST APIs
- Actual machine learning
- Explainable risk detection
- Secure authentication
- Automated testing
- Containerised deployment
- Professional user experience

Prioritise correctness, security, reliability and maintainability over speed.
