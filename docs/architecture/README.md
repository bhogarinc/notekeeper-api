# NoteKeeper System Architecture

## 1. Architecture Overview

### 1.1 System Context
NoteKeeper is a secure note-taking application built as a modular monolith with a modern React frontend and FastAPI backend.

### 1.2 Architecture Style: Modular Monolith

- **Pattern:** Clean Architecture / Hexagonal Architecture
- **Frontend:** Single Page Application (SPA) with React
- **Backend:** RESTful API with FastAPI
- **Database:** PostgreSQL with Redis caching
- **Deployment:** Containerized on Azure App Service

**Justification:**
- Small to medium team size - monolith reduces operational complexity
- Faster time to market with single deployable unit
- FastAPI's async support and automatic OpenAPI docs
- Clean modular design allows extraction to microservices if needed
- Cost efficiency with single Azure App Service instance

---

## 2. Container Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Client Layer                                               │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Web Browser  │  │Mobile Browser│                        │
│  └──────┬───────┘  └──────┬───────┘                        │
└─────────┼─────────────────┼─────────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure Front Door (CDN / WAF)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────────┐      ┌───────────────────┐
│  React SPA        │      │  FastAPI API      │
│  Nginx Container  │      │  Python Container │
└─────────┬─────────┘      └─────────┬─────────┘
          │                          │
          │    ┌─────────────────┐   │
          └───▶│  API Gateway    │◀──┘
               └─────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │    Azure     │
│   Database   │ │    Cache     │ │   Monitor    │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Container Responsibilities

| Container | Technology | Responsibility |
|-----------|------------|----------------|
| Web Application | React 18 + Vite | User interface, state management |
| API Application | FastAPI (Python 3.11) | Business logic, data access |
| Database | PostgreSQL 15 | Persistent data storage |
| Cache | Redis 7 | Session storage, query caching |
| Search Engine | PostgreSQL Full-Text | Note content search |

---

## 3. Technology Stack

### 3.1 Frontend Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | React | 18.x |
| Build Tool | Vite | 5.x |
| Language | TypeScript | 5.x |
| UI Library | Tailwind CSS + Headless UI | 3.x |
| State Management | Zustand | 4.x |
| HTTP Client | Axios | 1.x |
| Forms | React Hook Form + Zod | 7.x / 3.x |
| Markdown | React Markdown + Remark | 9.x |
| Icons | Lucide React | latest |
| Notifications | Sonner | latest |

### 3.2 Backend Stack

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.104+ |
| ASGI Server | Uvicorn | 0.24+ |
| ORM | SQLAlchemy 2.0 | 2.0+ |
| Migration | Alembic | 1.12+ |
| Authentication | python-jose + passlib | 3.3+ |
| Validation | Pydantic v2 | 2.5+ |
| Async Database | asyncpg | 0.29+ |
| Testing | pytest + pytest-asyncio | 7.x |
| Linting | ruff + mypy | latest |

### 3.3 Infrastructure Stack

| Category | Technology |
|----------|------------|
| Cloud Provider | Microsoft Azure |
| Compute | Azure App Service (Linux Containers) |
| Database | Azure Database for PostgreSQL |
| Cache | Azure Cache for Redis |
| Container Registry | Azure Container Registry |
| CDN | Azure Front Door |
| Monitoring | Azure Application Insights |
| Secrets | Azure Key Vault |
| CI/CD | GitHub Actions |

---

## 4. Data Architecture

### 4.1 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Notes table with soft delete
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    is_pinned BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    color VARCHAR(7) DEFAULT '#ffffff',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    search_vector tsvector
);

-- Categories
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#3b82f6',
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Tags
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) DEFAULT '#6b7280',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Junction tables
CREATE TABLE note_categories (
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, category_id)
);

CREATE TABLE note_tags (
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

-- Attachments
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions for refresh tokens
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_user_deleted ON notes(user_id, deleted_at);
CREATE INDEX idx_notes_search ON notes USING GIN(search_vector);
CREATE INDEX idx_notes_pinned ON notes(user_id, is_pinned, updated_at DESC);
CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_jti);
CREATE INDEX idx_sessions_user ON sessions(user_id, expires_at);
```

### 4.2 Caching Strategy

| Cache Type | Key Pattern | TTL | Invalidation |
|------------|-------------|-----|--------------|
| Session | `session:{jti}` | 24h | On logout |
| User Profile | `user:{user_id}` | 1h | On profile update |
| Note List | `notes:{user_id}:{page}:{filters}` | 5m | On note CRUD |
| Note Detail | `note:{note_id}` | 10m | On note update |
| Categories | `categories:{user_id}` | 15m | On category change |
| Tags | `tags:{user_id}` | 15m | On tag change |
| Rate Limit | `ratelimit:{ip}:{endpoint}` | 1m | Auto-expire |

---

## 5. Integration Architecture

### 5.1 API Design Principles

- **RESTful:** Standard HTTP methods, resource-based URLs
- **Versioned:** `/api/v1/` prefix for all endpoints
- **Consistent:** Standard response envelope
- **Documented:** Auto-generated OpenAPI/Swagger docs
- **Paginated:** Cursor-based pagination for lists

### 5.2 API Response Format

```json
{
  "success": true,
  "data": { },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "has_more": true
  },
  "error": null
}
```

### 5.3 Authentication Flow

1. User submits credentials to `/auth/login`
2. Backend validates credentials against hashed passwords (Argon2id)
3. JWT access token (15 min) and refresh token (7 days) issued
4. Access token sent in `Authorization: Bearer` header
5. Refresh token stored in httpOnly cookie
6. Token refresh endpoint rotates refresh tokens

### 5.4 External Service Integrations

| Service | Purpose | Integration Type |
|---------|---------|------------------|
| Azure AD | Optional SSO | OAuth2 / OpenID Connect |
| SendGrid | Email notifications | REST API |
| Azure Monitor | Logging & metrics | OpenTelemetry SDK |
| Azure Blob | File attachments | Azure SDK |

---

## 6. Deployment Architecture

### 6.1 Environment Strategy

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| Development | Local development | Docker Compose |
| Testing | CI/CD automated tests | GitHub Actions + Docker |
| Staging | Pre-production validation | Azure App Service (S1) |
| Production | Live application | Azure App Service (P1v2) |

### 6.2 CI/CD Pipeline

```
Push to main → Run Tests → Build Images → Push to ACR → Deploy Staging 
                                                                   ↓
Smoke Tests ← Deploy Production ← Integration Tests ←──────────────┘
```

---

## 7. Security Architecture

### 7.1 Defense in Depth

| Layer | Protection |
|-------|------------|
| Network | Azure DDoS Protection, NSGs |
| Edge | Azure Front Door WAF |
| Transport | TLS 1.3 Enforcement |
| Application | Input Validation (Pydantic) |
| Auth | JWT with short expiry |
| Data | Encryption at rest & in transit |

### 7.2 Security Headers

- Strict-Transport-Security
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Content-Security-Policy
- Referrer-Policy: strict-origin-when-cross-origin

### 7.3 Data Protection

- **Passwords:** Argon2id hashing
- **Tokens:** JWT with RS256 asymmetric signing
- **PII:** Encrypted at application layer
- **Secrets:** Azure Key Vault with managed identities

---

## 8. Monitoring & Observability

### 8.1 Three Pillars

| Pillar | Implementation |
|--------|----------------|
| Metrics | Prometheus + Azure Monitor Metrics |
| Logs | Structured JSON → Azure Log Analytics |
| Traces | OpenTelemetry → Application Insights |

### 8.2 Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time (p95) | < 200ms |
| Page Load Time | < 2s |
| Search Query Time | < 100ms |
| Availability SLA | 99.9% |

---

*Document Version: 1.0*
*Last Updated: System Architecture Phase*
