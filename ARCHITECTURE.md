# InsiderShield — System Architecture

## 1. Project Vision

InsiderShield is a professional, AI-powered insider threat detection and investigation platform for organizations. The platform helps security teams detect suspicious employee activity, identify behavioral anomalies, calculate explainable risk scores, and investigate potential insider threats.

**Target Users:** Security teams, IT security operations, compliance officers, and risk management personnel.

**Core Use Cases:**
- Detect anomalous employee activity (unusual logins, bulk downloads, privilege escalations)
- Calculate explainable risk scores with contributing factors
- Investigate potential insider threats with full audit trails
- Generate compliance reports for regulatory audits

## 2. System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend"
        UI[Next.js App Router]
        Auth[Authentication Layer]
        Dashboard[Security Dashboard]
        Alerts[Alert Console]
        Investigations[Investigation Interface]
        Reports[Report Generator]
    end
    
    subgraph "Backend Services"
        APIGateway[API Gateway / Reverse Proxy]
        AuthService[Authentication Service]
        UserManagementService[User & Org Management]
        EventAPI[Event Ingestion API]
        AnalyticsService[Analytics Service]
        MLService[ML & Risk Scoring Service]
        AlertAPI[Alert Management API]
        InvestigationAPI[Investigation API]
        MonitoringService[Monitoring & Health]
    end
    
    subgraph "Data Layer"
        Postgres[(PostgreSQL - Primary Database)]
        Redis[(Redis - Caching & Message Broker)]
    end
    
    subgraph "Background Processing"
        CeleryWorkers[Worker Pool]
    end
    
    UI --> Auth
    Auth --> AuthService
    UI --> Dashboard
    UI --> Alerts
    UI --> Investigations
    UI --> Reports
    
    Dashboard --> AnalyticsService
    Alerts --> AlertAPI
    Alerts --> InvestigationAPI
    Alerts --> MLService
    
    EventAPI --> AnalyticsService
    EventAPI --> MLService
    EventAPI --> Postgres
    
    AnalyticsService --> Postgres
    AnalyticsService --> Redis
    
    MLService --> Redis
    MLService --> Postgres
    
    AlertAPI --> Postgres
    AlertAPI --> Redis
    AlertAPI --> EventAPI
    
    InvestigationAPI --> Postgres
    InvestigationAPI --> AnalyticsService
    
    CeleryWorkers --> AnalyticsService
    CeleryWorkers --> MLService
    CeleryWorkers --> AlertAPI
    CeleryWorkers --> MonitoringService
    
    Postgres --> Redis
```

## 3. Technology Stack

### Core Technologies
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, React Query, Zustand
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy Core, Alembic
- **Database:** PostgreSQL 15+
- **ML:** Scikit-learn, Pandas, NumPy
- **Containerization:** Docker, Docker Compose
- **Background Jobs:** Celery with Redis broker

## 4. Database Schema & Relationships

### Core Tables

```sql
-- Organisations table - root of multi-tenancy (first)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    domain_pattern TEXT,
    subscription_tier TEXT NOT NULL DEFAULT 'free',
    compliance_level TEXT NOT NULL DEFAULT 'basic',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    settings JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT org_name_idx UNIQUE (name)
);

-- Users table - authentication system users (depends on organizations)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    department TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret TEXT,
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- User roles for RBAC (depends on organizations)
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- User role assignments (depends on users and roles)
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    assigned_by UUID NOT NULL REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- Employees table - business domain users (depends on organizations)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    employee_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    department TEXT NOT NULL,
    job_level TEXT NOT NULL,
    hire_date DATE NOT NULL,
    clearance_level TEXT DEFAULT 'standard',
    risk_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    baseline_risk DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Activity events - security-relevant actions (depends on organization and employee)
CREATE TABLE activity_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    source_ip TEXT,
    source_user_agent TEXT,
    resource_id TEXT,
    resource_type TEXT,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    file_size_bytes BIGINT,
    session_id TEXT,
    risk_score DECIMAL(5,2),
    anomaly_score DECIMAL(5,2),
    is_authorized BOOLEAN,
    metadata JSONB NOT NULL DEFAULT '{}',
    event_hash TEXT,
    processing_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Behavioral baselines for ML (depends on organization and employee)
CREATE TABLE behavior_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    baseline_type TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    mean_value DECIMAL(10,6) NOT NULL,
    std_dev DECIMAL(10,6) NOT NULL,
    min_value DECIMAL(10,6) NOT NULL,
    max_value DECIMAL(10,6) NOT NULL,
    data_points INTEGER NOT NULL,
    date_range_start TIMESTAMP WITH TIME ZONE NOT NULL,
    date_range_end TIMESTAMP WITH TIME ZONE NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Detection results from ML/AI analysis (depends on organization and employee)
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    event_id UUID REFERENCES activity_events(id) ON DELETE SET NULL,
    detection_type TEXT NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    anomaly_score DECIMAL(5,2) NOT NULL,
    contributing_features JSONB NOT NULL DEFAULT '{}',
    explanation TEXT,
    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    is_false_positive BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT
);

-- Risk scores calculated by ML system (depends on organization and employee)
CREATE TABLE risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    score DECIMAL(5,2) NOT NULL,
    score_level TEXT NOT NULL,
    contributing_factors JSONB NOT NULL DEFAULT '{}',
    model_version TEXT NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Investigation sessions (depends on organization, alert, investigator)
CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    investigator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    findings TEXT,
    actions_taken TEXT,
    evidence_collected TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'in_progress'
);

-- Security alerts generated from detections (depends on organization, employee, detection)
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    investigation_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Audit logs for compliance and security (depends on organization, user)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    ip_address TEXT,
    user_agent TEXT,
    request_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'
);

-- ML model versions for reproducibility (depends on organization)
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_type TEXT NOT NULL,
    version TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    accuracy DECIMAL(5,4),
    precision DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    false_positive_rate DECIMAL(5,4),
    model_path TEXT NOT NULL,
    training_config JSONB NOT NULL DEFAULT '{}',
    feature_list JSONB NOT NULL DEFAULT '[]',
    trained_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Synthetic scenarios for testing and evaluation (depends on organization)
CREATE TABLE synthetic_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    scenario_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity_level TEXT NOT NULL,
    expected_detection_rate DECIMAL(5,4),
    sample_events JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ML model versions for reproducibility (depends on organization)
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_type TEXT NOT NULL,
    version TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    accuracy DECIMAL(5,4),
    precision DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    false_positive_rate DECIMAL(5,4),
    model_path TEXT NOT NULL,
    training_config JSONB NOT NULL DEFAULT '{}',
    feature_list JSONB NOT NULL DEFAULT '[]',
    trained_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Synthetic scenarios for testing and evaluation (depends on organization)
CREATE TABLE synthetic_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    scenario_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity_level TEXT NOT NULL,
    expected_detection_rate DECIMAL(5,4),
    sample_events JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### Database Constraints & Indexes

```sql
-- Create indexes for performance
CREATE INDEX idx_activity_events_org_time ON activity_events(organization_id, event_timestamp);
CREATE INDEX idx_activity_events_employee_time ON activity_events(employee_id, event_timestamp);
CREATE INDEX idx_behavior_baselines_org_emp ON behavior_baselines(organization_id, employee_id);
CREATE INDEX idx_detections_org_time ON detections(organization_id, detection_timestamp);
CREATE INDEX idx_detections_employee_time ON detections(employee_id, detection_timestamp);
CREATE INDEX idx_risk_scores_org_emp ON risk_scores(organization_id, employee_id);
CREATE INDEX idx_users_org_active ON users(organization_id, is_active);
CREATE INDEX idx_alerts_org_emp_status ON alerts(organization_id, employee_id, status);
CREATE INDEX idx_alerts_employee_time ON alerts(employee_id, created_at);
CREATE INDEX idx_audit_logs_org_time ON audit_logs(organization_id, timestamp);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, timestamp);

-- Define unique constraints properly
CREATE UNIQUE INDEX uk_users_org_username ON users(organization_id, username);
CREATE UNIQUE INDEX uk_users_email ON users(email);
CREATE UNIQUE INDEX uk_employees_org_id ON employees(organization_id, employee_id);
CREATE UNIQUE INDEX uk_employees_org_email ON employees(organization_id, email);
CREATE UNIQUE INDEX uk_org_name ON organizations(name);

-- Allow multiple alerts for same employee/timestamp
CREATE INDEX idx_alerts_employee_timestamp ON alerts(employee_id, created_at);

-- Allow multiple detections for same employee/timestamp  
CREATE INDEX idx_detections_employee_timestamp ON detections(employee_id, detection_timestamp);

-- Allow multiple audit logs per employee/timestamp
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
```

### Multi-Tenant Isolation with RLS

```sql
-- Database roles for authentication
CREATE ROLE app_service_user WITH LOGIN;
CREATE ROLE authenticated_users WITH NOLOGIN;

-- Grant execute privileges
GRANT CONNECT ON DATABASE insidershield TO app_service_user;
GRANT USAGE ON SCHEMA public TO app_service_user, authenticated_users;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated_users;

-- Enable RLS on tenant-sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE behavior_baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Secure RLS policies (only allow access to user's own organization)
CREATE POLICY users_org_isolation ON users
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY employees_org_isolation ON employees
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY activity_events_org_isolation ON activity_events
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY alerts_org_isolation ON alerts
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY detections_org_isolation ON detections
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY investigations_org_isolation ON investigations
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY audit_logs_org_isolation ON audit_logs
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY risk_scores_org_isolation ON risk_scores
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY behavior_baselines_org_isolation ON behavior_baselines
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY organizations_access_policy ON organizations
    FOR SELECT
    TO authenticated_users
    USING (true);
```

## 5. Security Architecture

### Authentication & Authorization

#### Authentication Flow
```python
# JWT Configuration
JWT_CONFIG = {
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7,
    "algorithm": "RS256",
    "public_key_path": "/etc/ssl/public.key",
    "private_key_path": "/etc/ssl/private.key"
}

# Password Hashing
PASSWORD_CONFIG = {
    "algorithm": "argon2id",
    "time_cost": 3,
    "memory_cost": 65536,
    "parallelism": 4,
    "hash_len": 32,
    "salt_len": 16
}
```

#### Role-Based Access Control (RBAC)

**Core Roles:**
- `SUPER_ADMIN`: Full system access across all organizations
- `ORG_ADMIN`: Organization management, employee management, security monitoring
- `SECURITY_ANALYST`: Event review, alert investigation, report generation
- `AUDITOR`: Read-only access to reports and audit logs
- `EMPLOYEE`: Self-service profile, limited activity view

#### Organization Context Management

```python
@app.middleware("http")
async def organization_context(request: Request, call_next):
    token = request.headers.get("authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        
        # Get user's organizations
        user_orgs = await get_user_organizations(payload["sub"])
        
        if "organization_id" in request.path_params:
            requested_org = request.path_params["organization_id"]
            if requested_org not in user_orgs:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Set PostgreSQL context using connection callback
            await set_postgresql_context(request, requested_org)
    
    response = await call_next(request)
    return response

async def set_postgresql_context(request: Request, organization_id: UUID):
    # Set organization context for current database connection
    connection = request.state.db
    await connection.execute(
        "SET app.current_organization_id = %s", 
        str(organization_id)
    )
```

#### Session Security

```python
# Refresh Token Rotation
async def rotate_refresh_token(user_id: UUID, old_token: str):
    new_token = create_refresh_token(user_id)
    await store_token_in_redis(user_id, new_token, expires=7 DAYS)
    await blacklist_token_in_redis(user_id, old_token)
    return new_token

# Rate Limiting
@router.post("/api/v1/events")
@rate_limit(key=lambda r: r.client.host, limit=100, period=3600)
async def ingest_events(request: Request, events: List[ActivityEventCreate]):
    # Event processing logic
    pass
```

#### Authentication & Authorization (CORRECTED)

**Core Roles:**
- `SUPER_ADMIN`: Full system access across all organizations
- `ORG_ADMIN`: Organization management, employee management, security monitoring
- `SECURITY_ANALYST`: Event review, alert investigation, report generation
- `AUDITOR`: Read-only access to reports and audit logs
- `EMPLOYEE`: Self-service profile, limited activity view

#### PostgreSQL Database Roles and Grants
```sql
-- Database roles for authentication
CREATE ROLE app_service_user WITH LOGIN;
CREATE ROLE authenticated_users WITH NOLOGIN;
CREATE ROLE admin_user WITH NOLOGIN;

-- Grant execute privileges
GRANT CONNECT ON DATABASE insidershield TO app_service_user;
GRANT USAGE ON SCHEMA public TO app_service_user, authenticated_users, admin_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated_users;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_user;

-- Enable RLS on tenant-sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE behavior_baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_dead_letter_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE synthetic_scenarios ENABLE ROW LEVEL SECURITY;

-- Secure RLS policies (only allow access to user's own organization)
CREATE POLICY users_org_isolation ON users
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY employees_org_isolation ON employees
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY activity_events_org_isolation ON activity_events
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY alerts_org_isolation ON alerts
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY detections_org_isolation ON detections
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY investigations_org_isolation ON investigations
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY audit_logs_org_isolation ON audit_logs
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY risk_scores_org_isolation ON risk_scores
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY behavior_baselines_org_isolation ON behavior_baselines
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY organizations_access_policy ON organizations
    FOR SELECT
    TO authenticated_users
    USING (current_setting('app.current_organization_id'::text) IS NOT NULL);

CREATE POLICY roles_org_isolation ON roles
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY user_roles_org_isolation ON user_roles
    FOR ALL
    TO authenticated_users
    USING (
        EXISTS (SELECT 1 FROM users WHERE id = user_roles.user_id AND 
                organization_id = current_setting('app.current_organization_id'::text)) AND
        EXISTS (SELECT 1 FROM roles WHERE id = user_roles.role_id AND 
                organization_id = current_setting('app.current_organization_id'::text))
    );

CREATE POLICY event_outbox_org_isolation ON event_outbox
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY event_dead_letter_queue_org_isolation ON event_dead_letter_queue
    FOR ALL
    TO authenticated_users
    USING (
        EXISTS (SELECT 1 FROM event_outbox WHERE id = event_dead_letter_queue.outbox_id AND 
                organization_id = current_setting('app.current_organization_id'::text))
    );

CREATE POLICY ml_models_org_isolation ON ml_models
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));

CREATE POLICY synthetic_scenarios_org_isolation ON synthetic_scenarios
    FOR ALL
    TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id'::text));
```

#### Authentication & Authorization (CORRECTED)

**Core Roles:**
- `SUPER_ADMIN`: Full system access across all organizations
- `ORG_ADMIN`: Organization management, employee management, security monitoring
- `SECURITY_ANALYST`: Event review, alert investigation, report generation
- `AUDITOR`: Read-only access to reports and audit logs
- `EMPLOYEE`: Self-service profile, limited activity view

#### Organization Context Management (CORRECTED)

```python
async def get_current_user(request: Request):
    """Extract and validate JWT token from request and establish tenant context"""
    token = request.headers.get("authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication")
    
    token = token[7:]
    
    # Validate JWT with algorithm and signature verification
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_signature": True, "verify_exp": True},
            audience="insidershield-api",
            issuer="insidershield-auth"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    
    # Get user from database
    user_repository = UserRepository()
    user = await user_repository.get_by_id(UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Verify organization membership
    if "organization_id" in request.path_params:
        requested_org = UUID(request.path_params["organization_id"])
        user_orgs = await user_repository.get_organizations(user.id)
        
        if requested_org not in user_orgs:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Set tenant context using database function
        await set_postgresql_tenant_context(request, requested_org)
    
    return user

async def set_postgresql_tenant_context(request: Request, organization_id: UUID):
    # Use set_config for PostgreSQL session variable
    connection = request.state.db
    await connection.execute(
        "SELECT set_config('app.current_organization_id', %s, true)",
        str(organization_id)
    )
```

#### FastAPI Dependencies for Organization Context
```python
from fastapi import Depends, HTTPException, Request
from typing import Optional, List

async def get_current_user_with_tenant(
    request: Request,
    user_repository: UserRepository = Depends()
):
    """Dependency that validates user and establishes organization context"""
    return await get_current_user(request)

async def get_organization_id(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Optional[UUID]:
    """Extract and validate organization ID from request path"""
    if "organization_id" not in request.path_params:
        return None
    
    requested_org = UUID(request.path_params["organization_id"])
    
    # Verify user has access to this organization
    user_orgs = await user_repository.get_organizations(current_user.id)
    
    if requested_org not in user_orgs:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return requested_org
```

## 6. Event Processing Architecture

### Event Ingestion Pipeline

```mermaid
graph TD
    A[Client Application] --> B[API Gateway]
    B --> C[Event Ingestion API]
    C --> D{Idempotent Check} E[Event Store]
    C --> F{Valid Event?} G[Dead Letter Queue]
    D --> H[Async Processing Queue]
    H --> I[ML Processing]
    
    subgraph "Ingestion Processing"
        C
        D
        G
    end
    
    subgraph "ML Processing"
        H
        I
    end
```

### Event Lifecycle Management

#### Ingestion API with Outbox Pattern
```python
@app.post("/api/v1/organizations/{org_id}/events")
async def ingest_events(
    org_id: UUID,
    events: List[ActivityEventCreate],
    request: Request,
    current_user: User = Depends(get_current_user)
):
    db = request.state.db
    
    try:
        # Begin transaction
        async with db.begin() as transaction:
            # Idempotency check
            processed_event_ids = []
            duplicate_count = 0
            
            for event in events:
                event_hash = calculate_event_hash(event)
                
                # Check for duplicates within same transaction
                existing_event = await db.execute(
                    "SELECT id FROM activity_events WHERE event_hash = %s AND organization_id = %s",
                    event_hash, org_id
                )
                
                if existing_event.fetchone():
                    duplicate_count += 1
                    continue
                
                # Store event in outbox table
                outbox_id = await db.execute(
                    "INSERT INTO event_outbox (event_data, organization_id, user_id, event_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                    {
                        "event_type": event.event_type,
                        "event_timestamp": event.event_timestamp,
                        "employee_id": event.employee_id,
                        "metadata": event.metadata,
                        "source_ip": event.source_ip
                    }, org_id, current_user.id, event_hash
                )
                
                processed_event_ids.append(str(outbox_id))
            
            # Commit transaction
            await transaction.commit()
        
        # Dispatch to Celery workers via outbox
        for outbox_id in processed_event_ids:
            await dispatch_to_celery.delay("process_stored_event", outbox_id)
        
        return {
            "event_ids": processed_event_ids,
            "duplicates": duplicate_count,
            "rejected": len(events) - len(processed_event_ids) - duplicate_count
        }
        
    except Exception as e:
        logger.error(f"Event ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Event ingestion failed")
```

#### Event Processing Service
```python
# Celery task with reliable retry logic
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_stored_event(self, outbox_id: UUID):
    try:
        db = create_db_connection()
        
        # Retrieve event from outbox
        outbox_event = db.execute(
            "SELECT id, event_data, organization_id FROM event_outbox WHERE id = %s FOR UPDATE",
            outbox_id
        ).fetchone()
        
        if not outbox_event:
            logger.error(f"Outbox event not found: {outbox_id}")
            return
        
        event_data = outbox_event.event_data
        org_id = outbox_event.organization_id
        
        # Process event through ML pipeline
        risk_score = calculate_risk_score(event_data, org_id)
        detection = create_detection(event_data, risk_score, org_id)
        create_alert(detection, org_id)
        
        # Mark as processed
        db.execute(
            "UPDATE event_outbox SET processed_at = NOW(), process_retries = process_retries + 1 WHERE id = %s",
            outbox_id
        )
        
        # Clean up old processed events
        cleanup_old_outbox_events()
        
    except Exception as e:
        logger.error(f"Error processing outbox event {outbox_id}: {e}")
        
        # Move to dead letter queue after retries exhausted
        if self.request.retries >= 3:
            db.execute(
                "INSERT INTO event_dead_letter_queue (outbox_id, error_message, timestamp) VALUES (%s, %s, NOW())",
                outbox_id, str(e)
            )
            db.execute("DELETE FROM event_outbox WHERE id = %s", outbox_id)
        
        raise self.retry(exc=e)
```

#### Event Processing Tables (CORRECTED WITH COMPOSITION)
```sql
-- Event outbox for reliable event processing with same-organization foreign keys
CREATE TABLE event_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_data JSONB NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id, organization_id) ON DELETE CASCADE,
    event_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_outbox_organization (organization_id),
    INDEX idx_outbox_created_at (created_at),
    CONSTRAINT uk_event_outbox_org_hash UNIQUE (organization_id, event_hash)
);

-- Dead letter queue for failed events
CREATE TABLE event_dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outbox_id UUID NOT NULL REFERENCES event_outbox(id) ON DELETE CASCADE,
    error_message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    INDEX idx_dlq_timestamp (timestamp)
);

-- Index for concurrent processing of events
CREATE INDEX idx_event_outbox_processed_at ON event_outbox(processed_at) WHERE processed_at IS NULL;
```

#### Failure Scenarios

1. **Redis Unavailable**: Events stored in outbox table, Celery workers retry on connection recovery
2. **Worker Crash**: Celery auto-redrives failed tasks with exponential backoff (max 3 retries)
3. **Database Timeout**: Outbox pattern ensures at-least-once delivery
4. **DLQ Overflow**: Automated alerting and manual intervention required

## 7. Machine Learning Architecture

### Feature Extraction Pipeline

```python
class FeatureExtractor:
    def __init__(self, baseline_repository):
        self.baselines = baseline_repository
    
    async def extract_features(self, event: ActivityEvent, employee_id: UUID) -> Dict[str, float]:
        features = {}
        
        # Time-based features
        features["hour_of_day"] = event.event_timestamp.hour
        features["day_of_week"] = event.event_timestamp.weekday()
        
        # Behavioral features from baselines
        if employee_id:
            login_baseline = await self.baselines.get(employee_id, "login_time")
            if login_baseline:
                features["login_time_deviation"] = (
                    event.event_timestamp.hour - login_baseline.mean_value
                ) / login_baseline.std_dev
        
        # Security risk features
        features["privilege_escalation_attempt"] = 1.0 if event.action == "escalate_privileges" else 0.0
        features["unauthorized_file_access"] = 1.0 if not event.is_authorized else 0.0
        
        return features
```

### ML Model Architecture

#### Isolation Forest Implementation

```python
class AnomalyDetector:
    def __init__(self, model_path: Optional[str] = None):
        self.model = IsolationForest(
            n_estimators=200,
            max_samples="auto",
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        self.feature_scaler = StandardScaler()
        self.feature_imputer = SimpleImputer(strategy="median")
        
        if model_path:
            self.load_model(model_path)
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        # Split into training and validation sets (80-20)
        from sklearn.model_selection import train_test_split
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        
        # Preprocess data
        X_train_scaled = self.feature_scaler.fit_transform(X_train_split)
        X_val_scaled = self.feature_scaler.transform(X_val_split)
        X_train_processed = self.feature_imputer.fit_transform(X_train_scaled)
        X_val_processed = self.feature_imputer.transform(X_val_scaled)
        
        # Train model on training set
        self.model.fit(X_train_processed)
        
        # Evaluate on validation set (not training set)
        y_pred_val = self.model.predict(X_val_processed)
        y_scores_val = self.model.decision_function(X_val_processed)
        
        self.calculate_model_metrics(y_val_split, y_pred_val, y_scores_val)
    
    def predict_anomaly(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X_scaled = self.feature_scaler.transform(X)
        X_processed = self.feature_imputer.transform(X_scaled)
        
        # Isolation Forest returns:
        # -1 for anomalies (outliers), 1 for normal points (inliers)
        # decision_function returns anomaly scores (lower = more anomalous)
        predictions = self.model.predict(X_processed)
        anomaly_scores = self.model.decision_function(X_processed)
        
        # Convert to 0-100 scale where 100 = most anomalous
        normalized_scores = self.normalize_anomaly_scores(anomaly_scores)
        
        return predictions, normalized_scores
    
    def explain_anomaly(self, event: ActivityEvent, features: Dict[str, float]) -> Dict[str, Any]:
        # Isolation Forest does NOT provide native feature importance
        # Manual explanation based on feature values vs baselines
        
        contributing_factors = {}
        
        # Check feature deviations from baselines
        if "login_time_deviation" in features:
            deviation = features["login_time_deviation"]
            if abs(deviation) > 2:  # 2 standard deviations from mean
                contributing_factors["unusual_login_time"] = {
                    "value": deviation,
                    "impact": "high" if abs(deviation) > 3 else "medium",
                    "threshold": "±2 standard deviations"
                }
        
        if features.get("privilege_escalation_attempt", 0) == 1:
            contributing_factors["privilege_escalation"] = {
                "value": "attempted",
                "impact": "critical",
                "threshold": "any privilege escalation"
            }
        
        return {
            "contributing_factors": contributing_factors,
            "has_ml_prediction": True,
            "isolation_forest_score": features.get("isolation_score", 0)
        }
```

### Risk Scoring Engine

```python
class RiskScorer:
    def __init__(self, ml_detector: AnomalyDetector, rule_engine: RuleEngine):
        self.ml_detector = ml_detector
        self.rule_engine = rule_engine
        self.model_version = self.get_current_model_version()
        self.risk_calculator = RiskCalculator()
    
    async def calculate_risk_score(self, event: ActivityEvent, employee_id: UUID) -> RiskScore:
        # Extract features
        features = await self.feature_extractor.extract_features(event, employee_id)
        
        # Add Isolation Forest score
        features["isolation_score"] = self.calculate_isolation_score(features)
        
        # Get ML prediction
        ml_prediction, anomaly_score = self.ml_detector.predict_anomaly(
            pd.DataFrame([features])
        )
        
        # Get rule-based assessment
        rule_scores = await self.rule_engine.evaluate(event)
        
        # Combine signals using calibrated weights
        final_score = self.risk_calculator.calculate_weighted_score(
            ml_score=anomaly_score[0],
            rule_scores=rule_scores,
            event_type=event.event_type,
            employee_baseline=self.get_employee_baseline(employee_id)
        )
        
        # Generate explanations
        explanations = self.generate_explanations(
            features, ml_prediction[0], rule_scores
        )
        
        return RiskScore(
            score=final_score,
            level=self.classify_risk_level(final_score),
            contributing_factors=explanations,
            model_version=self.model_version,
            anomaly_score=anomaly_score[0],
            is_ml_detected=(ml_prediction[0] == -1)
        )
    
    def calculate_isolation_score(self, features: Dict[str, float]) -> float:
        # Calculate Isolation Forest score based on feature anomalies
        # This is a custom implementation since Isolation Forest doesn't provide native scores
        anomaly_indicators = []
        
        if "login_time_deviation" in features:
            anomaly_indicators.append(abs(features["login_time_deviation"]))
        
        if features.get("privilege_escalation_attempt", 0) == 1:
            anomaly_indicators.append(1.0)
        
        return min(sum(anomaly_indicators) / len(anomaly_indicators) * 100, 100) if anomaly_indicators else 0
```

### Model Evaluation

```python
async def evaluate_with_synthetic_scenarios():
    """Run model evaluation using labelled synthetic scenarios"""
    scenarios = await synthetic_scenario_repository.get_all()
    evaluation_results = []
    
    for scenario in scenarios:
        # Generate events for this scenario
        events = await generate_synthetic_events(scenario)
        
        # Process events through ML pipeline
        for event in events:
            risk_score = await risk_scorer.calculate_risk_score(event, scenario.employee_id)
            
            # Check if model detected the anomaly (based on risk score threshold)
            is_detection = risk_score.score >= 75  # High-risk threshold
            
            evaluation_results.append({
                "scenario_id": scenario.id,
                "event_id": event.id,
                "predicted": is_detection,
                "actual": scenario.is_anomaly,
                "risk_score": risk_score.score,
                "detection_confidence": risk_score.anomaly_score,
                "contributing_factors": risk_score.contributing_factors
            })
    
    # Calculate aggregate metrics
    metrics = calculate_evaluation_metrics(evaluation_results)
    
    # Store metrics in model_versions table
    await store_model_metrics(metrics, scenario.model_version)
    
    return metrics
```

## 8. API Design & Contracts

### Authentication APIs

```yaml
/post/api/v1/auth/login
  post:
    summary: User authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              username:
                type: string
              password:
                type: string
                format: password
    responses:
      '200':
        description: Successful authentication
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
                expires_in:
                  type: integer
                user:
                  $ref: '#/components/schemas/User'
      '401':
        description: Invalid credentials

/get/api/v1/auth/me
  get:
    summary: Get current user information
    security:
      - bearerAuth: []
    responses:
      '200':
        description: User information
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
```

### Event APIs

```yaml
/post/api/v1/organizations/{org_id}/events
  post:
    summary: Ingest employee activity events
    parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: array
            items:
              $ref: '#/components/schemas/ActivityEventCreate'
    responses:
      '202':
        description: Events accepted for processing
        content:
          application/json:
            schema:
              type: object
              properties:
                event_ids:
                  type: array
                  items:
                    type: string
                    format: uuid
                duplicates:
                  type: integer
                rejected:
                  type: integer
      '400':
        description: Invalid event data
      '401':
        description: Unauthorized
      '403':
        description: Access denied
      '429':
        description: Rate limit exceeded

/get/api/v1/organizations/{org_id}/employees/{employee_id}/events
  get:
    summary: Get employee events with filtering
    parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: employee_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: start_time
        in: query
        schema:
          type: string
          format: date-time
      - name: end_time
        in: query
        schema:
          type: string
          format: date-time
      - name: event_type
        in: query
        schema:
          type: string
    security:
      - bearerAuth: []
    responses:
      '200':
        description: List of activity events
        content:
          application/json:
            schema:
              type: object
              properties:
                events:
                  type: array
                  items:
                    $ref: '#/components/schemas/ActivityEvent'
                total:
                  type: integer
                has_more:
                  type: boolean
```

### Analytics APIs

```yaml
/get/api/v1/organizations/{org_id}/dashboard
  get:
    summary: Get security dashboard data
    parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: timeframe
        in: query
        required: true
        schema:
          type: string
          enum: [daily, weekly, monthly, quarterly]
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Dashboard metrics
        content:
          application/json:
            schema:
              type: object
              properties:
                metrics:
                  type: object
                  properties:
                    total_events:
                      type: integer
                    anomalous_events:
                      type: integer
                    risk_distribution:
                      type: object
                    top_risk_employees:
                      type: array
                      items:
                        $ref: '#/components/schemas/EmployeeRisk'
                time_series:
                  type: array
                  items:
                    $ref: '#/components/schemas/TimeSeriesData'

/get/api/v1/organizations/{org_id}/risk-scores
  get:
    summary: Get risk scores with filtering
    parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: risk_level
        in: query
        schema:
          type: string
          enum: [low, medium, high, critical]
      - name: employee_id
        in: query
        schema:
          type: string
          format: uuid
    security:
      - bearerAuth: []
    responses:
      '200':
        description: Risk scores
        content:
          application/json:
            schema:
              type: object
              properties:
                risk_scores:
                  type: array
                  items:
                    $ref: '#/components/schemas/RiskScore'
                summary:
                  type: object
                  properties:
                    average_score:
                      type: number
                    distribution:
                      type: object
```

## 9. Infrastructure & Deployment

### Docker Configuration

#### Backend Dockerfile
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# Frontend Dockerfile
FROM node:20-alpine AS frontend

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY frontend/ ./

# Build application
RUN npm run build

# Install serving tools
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run serve
CMD ["serve", "-s", "build", "-l", "3000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/insidershield"
      REDIS_URL: "redis://redis:6379/0"
      CELERY_BROKER_URL: "redis://redis:6379/0"
      CELERY_RESULT_BACKEND: "redis://redis:6379/0"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
      - NEXT_PUBLIC_APP_URL=http://localhost:3000
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: insidershield
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Environment Configuration

#### .env.example
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/insidershield
POSTGRES_PASSWORD=change-this-password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
JWT_PUBLIC_KEY_PATH=./certs/public.key
JWT_PRIVATE_KEY_PATH=./certs/private.key
PASSWORD_ENCRYPTION_KEY=key16chars

# Application
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=info
MAX_WORKERS=4

# Rate Limiting
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_AUTH=50

# ML Model
ML_MODEL_PATH=./models/current_model.pkl
MODEL_UPDATE_SCHEDULE=0 30 * * *
```

## 10. Project Scope & Timeline

### MVP Definition (4-6 Week Timeline)

**Week 1-2: Core Foundation**
- [ ] Database schema setup with RLS
- [ ] User authentication and RBAC
- [ ] Basic API infrastructure
- [ ] Docker environment setup

**Week 3: Core Processing**
- [ ] Event ingestion with validation
- [ ] Employee management
- [ ] Basic behavioral baselines
- [ ] Initial ML model integration

**Week 4: Risk Scoring & Detection**
- [ ] Explainable risk scoring engine
- [ ] Alert system
- [ ] Investigation workflows
- [ ] Basic dashboard

**Week 5-6: Testing & Hardening**
- [ ] Comprehensive test suite
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation completion

### MVP Feature List

**Must-Have Features:**
1. User authentication with JWT and refresh tokens
2. Organization-based access control
3. Event ingestion with validation and deduplication
4. Behavioral baseline establishment
5. Basic anomaly detection using Isolation Forest
6. Risk scoring with explainable outputs
7. Alert generation and management
8. Investigation workflow
9. Audit logging for compliance
10. Basic analytics dashboard

### Non-MVP Features (Future Phases)

1. Advanced ML models (LSTM, GRU for time-series)
2. Real-time streaming processing
3. Advanced visualization and reporting
4. Integration with external identity providers
5. Automated model retraining pipelines
6. Advanced correlation analysis
7. Threat intelligence integration
8. API marketplace for third-party extensions

## 11. Engineering Quality & Testing

### Testing Strategy

#### Unit Tests
```python
# tests/unit/test_ml_detector.py
import pytest
from unittest.mock import Mock, patch
from app.ml.detector import AnomalyDetector

class TestAnomalyDetector:
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    def test_predict_anomaly(self, detector):
        # Test prediction logic
        features = {"login_time": 14, "resource_access": 5}
        prediction, score = detector.predict_anomaly(features)
        assert prediction in [-1, 1]  # -1 = anomaly, 1 = normal
        assert 0 <= score <= 100
```

#### Integration Tests
```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient

class TestEventAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_ingest_event(self, client, auth_headers):
        event_data = {
            "employee_id": "uuid",
            "event_type": "login",
            "event_timestamp": "2024-01-01T14:00:00Z",
            "outcome": "success"
        }
        
        response = client.post(
            "/api/v1/organizations/{org_id}/events",
            json=[event_data],
            headers=auth_headers
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "event_ids" in data
```

#### Security Tests
```python
# tests/security/test_tenant_isolation.py
import pytest
from fastapi.testclient import TestClient

class TestTenantIsolation:
    @pytest.fixture
    def admin_client(self):
        # Create admin user in org1
        pass
    
    @pytest.fixture
    def analyst_client(self):
        # Create analyst user in org2
        pass
    
    def test_admin_cannot_access_other_org(self, admin_client, analyst_client):
        # Create event in org2
        event_data = {
            "employee_id": "uuid2",
            "event_type": "login",
            "outcome": "success"
        }
        
        response = analyst_client.post(
            "/api/v1/organizations/org2/events",
            json=[event_data]
        )
        
        # Should be denied
        assert response.status_code == 403
```

### Security Checklist

- [ ] SQL injection prevention
- [ ] JWT token validation
- [ ] Password hashing with Argon2id
- [ ] Rate limiting implementation
- [ ] Input validation and sanitization
- [ ] CORS configuration
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] Error handling without information leakage
- [ ] API endpoint authentication
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Dependency vulnerability scanning
- [ ] Container security scanning

## 12. Development Milestones & Risks

### Technical Risks & Mitigation

1. **Data Quality Issues**
   - **Risk**: Incomplete or incorrect event data affects ML model accuracy
   - **Mitigation**: Automated data validation, monitoring of event completeness, manual review of anomalous patterns
   - **Impact**: Poor model performance

2. **Model Drift**
   - **Risk**: ML model performance degrades over time
   - **Mitigation**: Automated retraining triggers, drift detection, continuous evaluation
   - **Impact**: Decreasing detection accuracy

3. **Performance Under Load**
   - **Risk**: System becomes slow or unavailable during peak usage
   - **Mitigation**: Horizontal scaling, load testing, caching strategies, database optimization
   - **Impact**: Slow response times

4. **Security Breaches**
   - **Risk**: Unauthorized access, data leaks, privilege escalation
   - **Mitigation**: Regular security audits, penetration testing, dependency scanning, security hardening
   - **Impact**: Data leaks, unauthorized access

5. **Integration Complexity**
   - **Risk**: System components fail to work together
   - **Mitigation**: Clear API contracts, interface testing, gradual integration, feature flags
   - **Impact**: System failures, data corruption

### Development Trade-offs

1. **ML vs Rules-Based Approach**
   - **Selected**: Hybrid approach combining ML with explicit security rules
   - **Reason**: Leverages pattern recognition while maintaining explainability and control

2. **Real-time vs Batch Processing**
   - **Selected**: Mixed approach - real-time for critical events, batch for periodic analysis
   - **Reason**: Balances detection speed with computational efficiency

3. **Monolithic vs Microservices**
   - **Selected**: Modular monolith for initial development
   - **Reason**: Easier deployment, better testability, maintains performance characteristics

### Folder Structure

```
/insidershield/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core business logic
│   │   ├── data/          # Data models and services
│   │   ├── ml/            # Machine learning components
│   │   ├── security/      # Security utilities
│   │   └── utils/         # Common utilities
│   ├── tasks/            # Celery tasks
│   ├── migrations/       # Database migrations
│   ├── tests/            # Application tests
│   └── config/           # Configuration
├── frontend/
│   ├── src/
│   │   ├── app/          # Application routes
│   │   ├── components/    # UI components
│   │   ├── services/      # API clients
│   │   ├── stores/        # State management
│   │   ├── utils/         # Helper functions
│   │   └── styles/        # Styling
│   ├── public/           # Static assets
│   └── tests/            # Frontend tests
├── docker/               # Docker configuration
├── monitoring/           # Monitoring configuration
├── docs/                 # Documentation
├── tests/               # Integration and end-to-end tests
└── scripts/              # Development scripts
```

## 13. Quality Gates

### Code Quality
- [ ] All code passes linting and formatting
- [ ] Type hints coverage > 90%
- [ ] Unit test coverage > 80%
- [ ] No security vulnerabilities in dependencies
- [ ] API documentation is auto-generated and up-to-date

### Security
- [ ] OWASP Top 10 addressed
- [ ] Penetration testing completed
- [ ] Security reviews for critical components
- [ ] Compliance checks for regulatory requirements

### Performance
- [ ] API response time < 500ms for 95% of requests
- [ ] Event processing throughput > 10,000 events/minute
- [ ] Memory usage < 1GB for typical deployment

### Reliability
- [ ] System availability > 99.9%
- [ ] Automated failover tested
- [ ] Disaster recovery procedures documented
- [ ] Backup and restore procedures tested

## 14. Conclusion

InsiderShield provides a comprehensive, secure, and scalable platform for insider threat detection and investigation. The architecture combines robust security controls, advanced machine learning capabilities, and professional user experience to deliver actionable insights for security teams.

The modular design ensures maintainability and extensibility, while the multi-tenant architecture supports organizational isolation and compliance requirements. The implementation focuses on real-world effectiveness through continuous model evaluation and improvement.

This architecture establishes a solid foundation for building a production-ready insider threat detection platform that can grow and adapt to evolving security challenges.