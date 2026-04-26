# NoteKeeper System Architecture

> **Quick Reference**: This document provides a high-level overview of the NoteKeeper system architecture. For detailed information, see the [docs/architecture](./docs/architecture) directory.

---

## 🏗️ Architecture Overview

**Architecture Style**: Modular Monolith with API-First Design

NoteKeeper uses a modular monolith architecture that balances simplicity and performance while maintaining clear boundaries for future scalability.

### Why Modular Monolith?

| Factor | Benefit |
|--------|---------|
| **Simplicity** | Single codebase reduces operational complexity |
| **Performance** | No network overhead between modules |
| **Consistency** | ACID transactions across all operations |
| **Deployment** | Single artifact to Azure App Service |
| **Evolution** | Clear boundaries allow future extraction to microservices |

---

## 📐 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Web App  │  │ Mobile   │  │  CLI     │                      │
│  │ (React)  │  │ (Future) │  │ (Future) │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       └─────────────┼─────────────┘                            │
│                     │                                          │
│                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              NoteKeeper REST API                         │   │
│  │         (FastAPI + Azure App Service)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                     │                                          │
└─────────────────────┼──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │ Azure Blob   │          │
│  │  (Primary)   │  │   (Cache)    │  │  (Files)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Module Structure

```
notekeeper/
├── modules/
│   ├── auth/           # JWT authentication, password hashing
│   ├── notes/          # CRUD, pinning, archiving, markdown
│   ├── categories/     # Hierarchy management
│   ├── tags/           # Tag CRUD and filtering
│   ├── search/         # Full-text search (PostgreSQL GIN)
│   └── users/          # Profile and preferences
├── core/               # Shared infrastructure
└── api/                # FastAPI routers
```

---

## 🛠️ Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11+ | Modern async support |
| Framework | FastAPI 0.104+ | High-performance API framework |
| ORM | SQLAlchemy 2.0+ | Async database operations |
| Migrations | Alembic 1.12+ | Database schema versioning |
| Auth | python-jose + bcrypt | JWT tokens and password hashing |
| Validation | Pydantic 2.5+ | Data validation and serialization |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18+ |
| Language | TypeScript 5+ |
| Styling | Tailwind CSS 3+ |
| State | Zustand 4+ |
| HTTP Client | Axios 1.6+ |

### Infrastructure
| Component | Service |
|-----------|---------|
| Compute | Azure App Service |
| Database | Azure Database for PostgreSQL |
| Cache | Azure Cache for Redis |
| Storage | Azure Blob Storage |
| Monitoring | Azure Monitor + Application Insights |

---

## 🔐 Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network                                             │
│ • Azure Firewall • DDoS Protection • NSGs                    │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Application                                         │
│ • HTTPS/TLS 1.3 • Rate Limiting • CORS • Security Headers   │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Authentication                                      │
│ • JWT (HS256) • bcrypt Password Hashing • Token Rotation    │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Data                                                │
│ • Encryption at Rest • Encryption in Transit • Key Vault    │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Audit                                               │
│ • Audit Logging • GDPR Compliance • Data Retention          │
└─────────────────────────────────────────────────────────────┘
```

### Authentication Flow
- **Access Tokens**: 15-minute expiry, memory storage
- **Refresh Tokens**: 7-day expiry, HTTP-only cookies
- **Token Rotation**: New refresh token issued with each access token refresh

---

## 📊 Data Architecture

### Core Entities

```
┌─────────┐     ┌─────────────┐     ┌─────────┐
│  User   │────▶│    Note     │◀────│   Tag   │
└────┬────┘     └──────┬──────┘     └─────────┘
     │                 │
     │            ┌────┴────┐
     └───────────▶│ Category│
                  └─────────┘
```

### Database Highlights
- **UUID Primary Keys** for all entities
- **JSONB Columns** for flexible metadata
- **GIN Indexes** for full-text search
- **Audit Logging** for compliance
- **Foreign Key Constraints** with CASCADE

### Caching Strategy

| Cache Type | Key Pattern | TTL | Purpose |
|------------|-------------|-----|---------|
| Session | `session:{user_id}` | 24h | Active sessions |
| Rate Limit | `ratelimit:{ip}` | 1m | API throttling |
| Note List | `notes:{user_id}:{page}` | 5m | Pagination cache |
| Search | `search:{user_id}:{hash}` | 2m | Search results |

---

## 🚀 Deployment Architecture

### Environment Strategy

| Environment | Purpose | Configuration |
|-------------|---------|---------------|
| **Development** | Local development | Docker Compose |
| **Staging** | Pre-production testing | Azure P1v3, 1-2 instances |
| **Production** | Live application | Azure P1v3, auto-scale 2-10 |

### CI/CD Pipeline

```
Commit → Build → Test → Deploy Staging → Smoke Tests → Deploy Production
```

### Auto-scaling Rules
- **Scale Up**: CPU > 70% for 5 minutes
- **Scale Down**: CPU < 30% for 10 minutes
- **Range**: 2-10 instances

---

## 📈 Performance Targets

| Metric | Target |
|--------|--------|
| API Response (p95) | < 200ms |
| Database Query (p95) | < 50ms |
| Search Response | < 100ms |
| Concurrent Users | 1000+ |
| Availability | 99.9% |

---

## 🗺️ Scalability Roadmap

### Phase 1: Launch (Current)
- Single Azure App Service instance
- Azure Database for PostgreSQL
- Azure Cache for Redis

### Phase 2: Growth (6-12 months)
- Auto-scaling (2-10 instances)
- PostgreSQL Hyperscale (Citus)
- Redis Cluster
- Read replicas

### Phase 3: Scale (12+ months)
- Azure Cognitive Search
- Microservices (if needed)
- Multi-region deployment
- Event-driven architecture

---

## 📚 Documentation

- **[System Architecture](./docs/architecture/system-architecture.md)** - Detailed architecture documentation
- **[Technology Decisions](./docs/architecture/technology-decisions.md)** - ADRs for all technology choices
- **[API Documentation](./docs/api)** - OpenAPI/Swagger documentation
- **[Deployment Guide](./docs/deployment)** - Infrastructure and deployment docs

---

## 🔗 Quick Links

- **GitHub Repository**: https://github.com/bhogarinc/notekeeper-api
- **API Documentation**: `/docs` (when running)
- **Staging Environment**: https://notekeeper-staging.azurewebsites.net
- **Production Environment**: https://notekeeper.azurewebsites.net

---

## 📝 Architecture Decisions

Key architectural decisions are recorded as Architecture Decision Records (ADRs):

1. **ADR-001**: Architecture Style - Modular Monolith
2. **ADR-002**: Backend Framework - FastAPI
3. **ADR-003**: Database - PostgreSQL
4. **ADR-004**: ORM - SQLAlchemy 2.0
5. **ADR-005**: Authentication - JWT with Refresh Tokens
6. **ADR-006**: Frontend - React with TypeScript
7. **ADR-007**: UI Framework - Tailwind CSS
8. **ADR-008**: Cache - Redis
9. **ADR-009**: Deployment - Azure App Service
10. **ADR-010**: CI/CD - GitHub Actions
11. **ADR-011**: Search - PostgreSQL Full-Text Search
12. **ADR-012**: API Versioning - URL Path
13. **ADR-013**: State Management - Zustand
14. **ADR-014**: Documentation - OpenAPI + Confluence

See [docs/architecture/technology-decisions.md](./docs/architecture/technology-decisions.md) for full details.

---

*Last Updated: 2024-01-02*
*Version: 1.0*
