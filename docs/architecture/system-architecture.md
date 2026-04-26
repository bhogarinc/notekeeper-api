# NoteKeeper System Architecture

## Overview

NoteKeeper is a secure note-taking REST API application built with a modern, scalable architecture. This document outlines the system design, technology choices, and deployment strategy.

## Architecture Style: Modular Monolith with API-First Design

### Justification

We chose a **Modular Monolith** architecture for NoteKeeper because:

1. **Simplicity**: Single codebase reduces operational complexity
2. **Performance**: No network overhead between services
3. **Data Consistency**: Single database with ACID transactions
4. **Deployment**: Single artifact deployment to Azure App Service
5. **Team Size**: Appropriate for small to medium development teams
6. **Future Evolution**: Well-defined module boundaries allow future extraction to microservices

### Module Boundaries

```
notekeeper/
├── modules/
│   ├── auth/           # Authentication & authorization
│   ├── notes/          # Note CRUD operations
│   ├── categories/     # Category management
│   ├── tags/           # Tag management
│   ├── search/         # Full-text search
│   └── users/          # User management
├── core/               # Shared infrastructure
└── api/                # API layer (FastAPI routers)
```

---

## System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SYSTEMS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│   │   Web App    │      │  Mobile App  │      │   CLI Tool   │             │
│   │   (React)    │      │  (Future)    │      │  (Future)    │             │
│   └──────┬───────┘      └──────┬───────┘      └──────┬───────┘             │
│          │                     │                     │                      │
│          └─────────────────────┼─────────────────────┘                      │
│                                │                                             │
│                                ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      NoteKeeper REST API                            │   │
│   │                    (FastAPI + Azure App Service)                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                             │
└────────────────────────────────┼─────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA & INFRASTRUCTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│   │  PostgreSQL  │    │    Redis     │    │ Azure Blob   │                 │
│   │  (Primary DB)│    │   (Cache)    │    │  (Backups)   │                 │
│   └──────────────┘    └──────────────┘    └──────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Container Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Azure App Service Container                           │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           FastAPI Application                          │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   Auth      │  │   Notes     │  │  Categories │  │    Tags     │   │  │
│  │  │   Module    │  │   Module    │  │   Module    │  │   Module    │   │  │
│  │  │             │  │             │  │             │  │             │   │  │
│  │  │ • JWT Auth  │  │ • CRUD Ops  │  │ • CRUD Ops  │  │ • CRUD Ops  │   │  │
│  │  │ • Password  │  │ • Pinning   │  │ • Hierarchy │  │ • Filtering │   │  │
│  │  │   Hashing   │  │ • Archiving │  │             │  │             │   │  │
│  │  │ • Token     │  │ • Markdown  │  │             │  │             │   │  │
│  │  │   Refresh   │  │   Render    │  │             │  │             │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   Search    │  │   Users     │  │   Common    │  │    API      │   │  │
│  │  │   Module    │  │   Module    │  │   Utils     │  │   Router    │   │  │
│  │  │             │  │             │  │             │  │             │   │  │
│  │  │ • Full-text │  │ • Profile   │  │ • Logging   │  │ • OpenAPI   │   │  │
│  │  │   Search    │  │ • Settings  │  │ • Validation│  │ • Swagger   │   │  │
│  │  │ • Indexing  │  │ • Preferences│ │ • Pagination│  │ • Version   │   │  │
│  │  │             │  │             │  │ • Errors    │  │   Control   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Middleware Layer                               │  │
│  │                                                                        │  │
│  │  • CORS Handler    • Rate Limiter    • Request Logger    • Auth Guard │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Access Layer                              │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │ SQLAlchemy  │  │   Alembic   │  │   Redis     │                    │  │
│  │  │   ORM       │  │  Migrations │  │   Client    │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Language | Python | 3.11+ | Modern async support, excellent FastAPI integration |
| Framework | FastAPI | 0.104+ | High performance, automatic OpenAPI docs, type hints |
| ORM | SQLAlchemy | 2.0+ | Mature, async support, PostgreSQL-specific features |
| Migrations | Alembic | 1.12+ | Official SQLAlchemy migration tool |
| Auth | python-jose | 3.3+ | JWT handling, industry standard |
| Password Hash | bcrypt | 4.1+ | Secure, well-tested |
| Validation | Pydantic | 2.5+ | Native FastAPI integration, v2 performance |
| HTTP Client | httpx | 0.25+ | Async HTTP client for external calls |

### Database & Storage

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Primary DB | PostgreSQL 15+ | Full-text search, JSONB support, ACID compliance |
| Cache | Redis 7+ | Session storage, rate limiting, query caching |
| Search Index | PostgreSQL GIN | Native full-text search, no additional infrastructure |
| File Storage | Azure Blob | Native Azure integration for backups/exports |

### Frontend

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Framework | React 18+ | Component-based, large ecosystem |
| Language | TypeScript 5+ | Type safety, better IDE support |
| UI Library | Tailwind CSS 3+ | Utility-first, customizable, small bundle |
| State Management | Zustand | Lightweight, TypeScript-friendly |
| HTTP Client | Axios | Interceptors, request/response transforms |
| Markdown | react-markdown | Safe markdown rendering |
| Icons | Lucide React | Modern, consistent icon set |

### Infrastructure

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Cloud Provider | Microsoft Azure | Specified requirement, excellent Python support |
| Compute | Azure App Service | Managed platform, auto-scaling, easy deployment |
| Database | Azure Database for PostgreSQL | Managed, backups, high availability |
| Cache | Azure Cache for Redis | Managed Redis service |
| CDN | Azure CDN | Static asset delivery |
| Monitoring | Azure Monitor + App Insights | Native integration |
| Secrets | Azure Key Vault | Secure secret management |

### DevOps & CI/CD

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Container | Docker | Consistent environments |
| Orchestration | Docker Compose (local) | Simple local development |
| CI/CD | GitHub Actions | Native GitHub integration, free for public repos |
| Testing | pytest | Python standard, async support |
| Linting | ruff | Fast, comprehensive Python linter |
| Formatting | black | Consistent code style |
| Type Checking | mypy | Static type analysis |

---

## Data Architecture

### Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Categories Table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6', -- Hex color code
    icon VARCHAR(50),
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Tags Table
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) DEFAULT '#6B7280',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Notes Table
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_html TEXT, -- Pre-rendered HTML for performance
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_encrypted BOOLEAN DEFAULT FALSE,
    encrypted_content BYTEA, -- For client-side encrypted notes
    metadata JSONB DEFAULT '{}', -- Flexible metadata storage
    word_count INTEGER DEFAULT 0,
    reading_time_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE
);

-- Note-Tags Junction Table
CREATE TABLE note_tags (
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (note_id, tag_id)
);

-- Full-text Search Index
CREATE INDEX idx_notes_fts ON notes 
USING GIN (to_tsvector('english', title || ' ' || COALESCE(content, '')));

-- Refresh Tokens Table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    device_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log Table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Data Flow Diagrams

#### Authentication Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │────▶│   Login     │────▶│   Verify    │────▶│   Generate  │
│         │     │   Endpoint  │     │  Password   │     │    Tokens   │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                               │
                                                               ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │◀────│  Return     │◀────│  Store      │◀────│   Access +  │
│         │     │  Tokens     │     │  Refresh    │     │   Refresh   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### Note Creation Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │────▶│   Validate  │────▶│   Process   │────▶│   Create    │
│         │     │   Request   │     │  Markdown   │     │   Record    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                               │
                                                               ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │◀────│   Return    │◀────│   Update    │◀────│   Commit    │
│         │     │   Note      │     │   Search    │     │   Transaction│
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### Search Flow

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │────▶│   Parse     │────▶│   Build     │────▶│   Execute   │
│         │     │   Query     │     │   SQL       │     │   Search    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                               │
                                                               ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │◀────│   Return    │◀────│   Apply     │◀────│   PostgreSQL│
│         │     │   Results   │     │   Filters   │     │   GIN Index │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Caching Strategy

| Cache Type | Key Pattern | TTL | Use Case |
|------------|-------------|-----|----------|
| Session | `session:{user_id}` | 24h | Active user sessions |
| Rate Limit | `ratelimit:{ip}` | 1m | API rate limiting |
| User Profile | `user:{user_id}` | 1h | User metadata |
| Note List | `notes:{user_id}:{page}` | 5m | Paginated note lists |
| Search Results | `search:{user_id}:{hash}` | 2m | Search queries |
| Category Tree | `categories:{user_id}` | 10m | User's category hierarchy |

---

## Integration Architecture

### API Gateway Design

FastAPI serves as the API gateway with the following middleware stack:

```python
# Middleware Order (outer to inner)
1. CORS Middleware          # Handle cross-origin requests
2. Trusted Host Middleware  # Validate host headers
3. Rate Limit Middleware    # Prevent abuse
4. Request ID Middleware    # Distributed tracing
5. Logging Middleware       # Request/response logging
6. Authentication Middleware # JWT validation
7. Exception Handler        # Global error handling
```

### API Versioning Strategy

```
/api/v1/notes          # Current stable version
/api/v2/notes          # Future version (when needed)
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     JWT Authentication Flow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Login                                                       │
│      POST /api/v1/auth/login                                     │
│      { email, password } ──▶ { access_token, refresh_token }     │
│                                                                  │
│   2. Authenticated Request                                       │
│      Authorization: Bearer {access_token}                        │
│      ──▶ Validate JWT ──▶ Extract user_id ──▶ Proceed            │
│                                                                  │
│   3. Token Refresh                                               │
│      POST /api/v1/auth/refresh                                   │
│      { refresh_token } ──▶ { access_token, refresh_token }       │
│                                                                  │
│   4. Logout                                                      │
│      POST /api/v1/auth/logout                                    │
│      ──▶ Revoke refresh_token ──▶ Clear session                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "iat": 1704067200,
  "exp": 1704070800,
  "type": "access",
  "jti": "unique-token-id"
}
```

### External Service Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| Azure Blob Storage | SDK | File attachments, exports |
| SendGrid (optional) | REST API | Email notifications |
| Azure Key Vault | SDK | Secret management |

---

## Deployment Architecture

### Environment Strategy

| Environment | Purpose | Data | Scaling |
|-------------|---------|------|---------|
| Development | Local development | Local PostgreSQL/Redis | Single instance |
| Staging | Pre-production testing | Azure PostgreSQL (small) | 1-2 instances |
| Production | Live application | Azure PostgreSQL (HA) | Auto-scaling 2-10 |

### Azure App Service Configuration

```yaml
# Production Configuration
app_service_plan:
  tier: PremiumV3
  size: P1v3
  instances:
    min: 2
    max: 10
  
app_settings:
  - WEBSITES_PORT: 8000
  - PYTHON_VERSION: 3.11
  - SCM_DO_BUILD_DURING_DEPLOYMENT: true
  
health_check:
  path: /api/v1/health
  interval: 60s
  
auto_scaling:
  rules:
    - metric: CpuPercentage
      threshold: 70
      operator: GreaterThan
      action: Increase
    - metric: CpuPercentage
      threshold: 30
      operator: LessThan
      action: Decrease
```

### Deployment Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Commit  │──▶│   Build  │──▶│   Test   │──▶│  Deploy  │──▶│  Verify  │
│  to main │   │  Docker  │   │   Suite  │   │  Staging │   │  Health  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └─────┬────┘
                                                                  │
                                                                  ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Notify  │◀──│  Monitor │◀──│  Smoke   │◀──│  Deploy  │◀──│  Manual  │
│  Success │   │  Metrics │   │   Tests  │   │Production│   │ Approval │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Monitoring and Logging Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Application Logs | Azure Monitor | Structured logging |
| Performance | Application Insights | APM, distributed tracing |
| Errors | Sentry (optional) | Error tracking |
| Uptime | Azure Monitor | Health checks, alerts |
| Metrics | Azure Monitor | Custom business metrics |

### Alert Configuration

```yaml
alerts:
  - name: High Error Rate
    condition: errors > 5% over 5 minutes
    severity: Critical
    
  - name: High Response Time
    condition: p95 latency > 500ms over 10 minutes
    severity: Warning
    
  - name: Database Connection Issues
    condition: failed_connections > 10 over 5 minutes
    severity: Critical
    
  - name: Low Disk Space
    condition: storage < 20%
    severity: Warning
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security                                       │
│  • Azure Firewall                                                │
│  • DDoS Protection                                               │
│  • Network Security Groups                                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Application Security                                   │
│  • HTTPS/TLS 1.3                                                 │
│  • Rate Limiting                                                 │
│  • Input Validation                                              │
│  • CORS Policy                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Authentication & Authorization                         │
│  • JWT Tokens (HS256)                                            │
│  • Password Hashing (bcrypt)                                     │
│  • Role-Based Access Control                                     │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Data Security                                          │
│  • Encryption at Rest (Azure-managed)                            │
│  • Encryption in Transit (TLS)                                   │
│  • Field-level Encryption (for sensitive notes)                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: Audit & Compliance                                     │
│  • Audit Logging                                                 │
│  • Data Retention Policies                                       │
│  • GDPR Compliance                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Security Headers

```python
# FastAPI Security Middleware
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

---

## Performance Considerations

### Optimization Strategies

| Area | Strategy | Implementation |
|------|----------|----------------|
| Database | Connection Pooling | SQLAlchemy async pool (20-100) |
| Database | Query Optimization | Selective columns, proper indexes |
| API | Response Caching | Redis for read-heavy endpoints |
| API | Pagination | Cursor-based for large datasets |
| Search | Full-text Index | PostgreSQL GIN index |
| Static | CDN | Azure CDN for frontend assets |
| Compression | Gzip/Brotli | Azure App Service native |

### Expected Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 200ms | Application Insights |
| Database Query Time (p95) | < 50ms | PostgreSQL logs |
| Search Response Time | < 100ms | Application Insights |
| Concurrent Users | 1000+ | Load testing |
| Availability | 99.9% | Azure Monitor |

---

## Scalability Roadmap

### Phase 1: Launch (Current)
- Single Azure App Service instance
- Azure Database for PostgreSQL (Single Server)
- Azure Cache for Redis (Basic)

### Phase 2: Growth (6-12 months)
- Auto-scaling App Service (2-10 instances)
- PostgreSQL Hyperscale (Citus) for horizontal scaling
- Redis Cluster for cache sharding
- Read replicas for query offloading

### Phase 3: Scale (12+ months)
- Extract search to Azure Cognitive Search
- Microservices for specific domains (if needed)
- Multi-region deployment for global users
- Event-driven architecture with Azure Service Bus

---

## Appendix A: API Endpoint Summary

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### Notes
- `GET /api/v1/notes` - List notes (paginated)
- `POST /api/v1/notes` - Create note
- `GET /api/v1/notes/{id}` - Get note
- `PUT /api/v1/notes/{id}` - Update note
- `DELETE /api/v1/notes/{id}` - Delete note
- `POST /api/v1/notes/{id}/pin` - Pin/unpin note
- `POST /api/v1/notes/{id}/archive` - Archive/unarchive note

### Categories
- `GET /api/v1/categories` - List categories
- `POST /api/v1/categories` - Create category
- `PUT /api/v1/categories/{id}` - Update category
- `DELETE /api/v1/categories/{id}` - Delete category

### Tags
- `GET /api/v1/tags` - List tags
- `POST /api/v1/tags` - Create tag
- `PUT /api/v1/tags/{id}` - Update tag
- `DELETE /api/v1/tags/{id}` - Delete tag

### Search
- `GET /api/v1/search?q={query}` - Full-text search

---

*Document Version: 1.0*
*Last Updated: 2024-01-02*
*Author: System Architect*
