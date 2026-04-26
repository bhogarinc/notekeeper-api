# System Architecture Overview

## NoteKeeper Architecture Documentation

This document describes the high-level architecture of the NoteKeeper application using the C4 Model approach.

---

## 1. System Context Diagram (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM CONTEXT                                  │
│                         NoteKeeper Application                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                    ┌─────────────────────┐
    │              │  HTTPS/REST        │                     │
    │   End User   │◄──────────────────►│    NoteKeeper       │
    │  (Browser)   │                    │    Application      │
    │              │                    │                     │
    └──────────────┘                    └──────────┬──────────┘
                                                   │
                          ┌───────────────────────┼───────────────────────┐
                          │                       │                       │
                          ▼                       ▼                       ▼
                   ┌────────────┐        ┌────────────┐          ┌────────────┐
                   │ PostgreSQL │        │   Redis    │          │ Azure Blob │
                   │  Database  │        │   Cache    │          │  Storage   │
                   └────────────┘        └────────────┘          └────────────┘
```

### Context Elements

| Element | Type | Description |
|---------|------|-------------|
| End User | Person | Users who create, edit, search, and manage notes through the web interface |
| NoteKeeper Application | Software System | The complete note-taking application including frontend SPA and REST API |
| PostgreSQL Database | External System | Primary data store for notes, users, categories, and tags |
| Redis Cache | External System | Session storage, query caching, and rate limiting |
| Azure Blob Storage | External System | File attachments and exported note archives |

---

## 2. Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           CONTAINER DIAGRAM                                         │
│                      NoteKeeper Application                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                           End User (Browser)                                │
    └───────────────────────────────┬─────────────────────────────────────────────┘
                                    │ HTTPS
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                           Azure App Service                                  │
    │  ┌───────────────────────────────────────────────────────────────────────┐  │
    │  │                         Web Container                                  │  │
    │  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
    │  │  │                    Single Page Application                       │  │  │
    │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
    │  │  │  │   Router    │  │   Store     │  │     UI Components       │  │  │  │
    │  │  │  │  (Vanilla)  │  │(EventEmitter│  │  (Custom Web Components)│  │  │  │
    │  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
    │  │  └─────────────────────────────────────────────────────────────────┘  │  │
    │  │                                    │                                    │  │
    │  │                                    │ REST API Calls                     │  │
    │  │                                    ▼                                    │  │
    │  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
    │  │  │                      API Container                               │  │  │
    │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
    │  │  │  │   Express   │  │   Prisma    │  │    Business Logic       │  │  │  │
    │  │  │  │   Server    │  │    ORM      │  │    (Services)           │  │  │  │
    │  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
    │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
    │  │  │  │   Zod       │  │   JWT       │  │    Rate Limiter         │  │  │  │
    │  │  │  │ Validation  │  │   Auth      │  │    (Redis)              │  │  │  │
    │  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │  │
    │  │  └─────────────────────────────────────────────────────────────────┘  │  │
    │  └───────────────────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌────────────┐  ┌────────────┐  ┌────────────┐
            │ PostgreSQL │  │   Redis    │  │ Azure Blob │
            │  Database  │  │   Cache    │  │  Storage   │
            └────────────┘  └────────────┘  └────────────┘
```

### Container Specifications

#### Web Container (SPA Frontend)
- **Technology**: Vanilla JavaScript, Custom Web Components
- **Build Tool**: Vite
- **Responsibilities**: UI rendering, client-side routing, state management
- **Deployment**: Served as static files from API container or CDN

#### API Container (Backend)
- **Technology**: Node.js 20, Express.js, TypeScript
- **Runtime**: Azure App Service Linux container
- **Responsibilities**: REST API endpoints, business logic, data access
- **Key Libraries**: Prisma ORM, Zod, jsonwebtoken, bcrypt

---

## 3. Architecture Style Decision

### Selected: Modular Monolith

After evaluating the requirements and constraints, we've selected a **Modular Monolith** architecture style.

### Decision Factors

| Factor | Assessment | Impact |
|--------|------------|--------|
| Team Size | Small team (2-3 developers) | Monolith reduces operational complexity |
| Time to Market | 6-8 week target | Monolith enables faster initial development |
| Complexity | Medium complexity domain | No need for microservices overhead |
| Scalability Needs | Moderate (1000s of users) | Vertical scaling sufficient initially |
| Data Consistency | Strong consistency required | Single database simplifies transactions |
| Deployment Complexity | Must be simple | Single deployable unit |

### Why NOT Microservices?

- **Operational Overhead**: Kubernetes, service mesh, distributed tracing too complex for initial release
- **Development Velocity**: Cross-service debugging and testing slows development
- **Data Consistency**: Notes, tags, and categories have tight coupling; distributed transactions add complexity
- **Team Size**: Microservices require dedicated teams per service

### Why NOT Serverless?

- **Cold Start Latency**: Unacceptable for user-facing note operations
- **Vendor Lock-in**: Azure Functions lock-in vs portable containers
- **Complexity**: Function composition and state management more complex than monolith
- **Cost**: Predictable traffic patterns make containers more cost-effective

### Modular Organization

Within the monolith, we maintain clear module boundaries:

```
src/
├── modules/
│   ├── auth/           # Authentication & authorization
│   ├── notes/          # Note CRUD and search
│   ├── categories/     # Category management
│   ├── tags/           # Tag management
│   └── attachments/    # File upload/download
├── shared/
│   ├── database/       # Prisma client, migrations
│   ├── cache/          # Redis client
│   ├── middleware/     # Common Express middleware
│   └── utils/          # Shared utilities
└── config/             # Environment configuration
```

---

## 4. Component Interactions

### Request Lifecycle

```
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────┐
│ Client  │────►│  Nginx   │────►│   Express   │────►│  Middleware  │
│ Request │     │ (Azure)  │     │   Server    │     │   Pipeline   │
└─────────┘     └──────────┘     └─────────────┘     └──────────────┘
                                                             │
           ┌─────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│   Zod Schema     │────►│   JWT Auth   │────►│ Rate Limiter │
│   Validation     │     │   Middleware │     │   (Redis)    │
└──────────────────┘     └──────────────┘     └──────────────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │   Service    │
                                              │   Handler    │
                                              └──────────────┘
                                                       │
           ┌───────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Prisma Client   │────►│ PostgreSQL   │────►│   Response   │
│   (ORM Query)    │     │   Database   │     │   (JSON)     │
└──────────────────┘     └──────────────┘     └──────────────┘
```

---

## 5. Scalability Strategy

### Current State (Monolith)
- **Vertical Scaling**: Increase App Service plan tier
- **Database**: Scale PostgreSQL compute/storage independently
- **Caching**: Redis reduces database load

### Future Evolution (If Needed)
1. **Read Replicas**: PostgreSQL read replicas for search queries
2. **CDN**: Azure CDN for static assets and API responses
3. **Background Jobs**: Azure Container Instances for exports/imports
4. **Service Extraction**: Extract search service if full-text search becomes bottleneck

---

## 6. Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Network                                                │
│  - HTTPS/TLS 1.3 for all communications                          │
│  - Azure DDoS Protection Standard                                │
│  - Private endpoints for database access                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Application                                            │
│  - JWT authentication with short-lived access tokens             │
│  - Refresh token rotation                                        │
│  - Rate limiting per user/IP                                     │
│  - Input validation with Zod schemas                             │
│  - SQL injection protection via parameterized queries (Prisma)   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Data                                                   │
│  - Password hashing with bcrypt (cost factor 12)                 │
│  - AES-256 encryption for sensitive note content (optional)      │
│  - Row-level security policies in PostgreSQL                     │
│  - Encrypted backups                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Technology Summary

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| Runtime | Node.js | 20 LTS | Long-term support, modern features |
| Framework | Express.js | 4.x | Mature, well-documented, middleware ecosystem |
| Language | TypeScript | 5.x | Type safety, better DX, fewer runtime errors |
| ORM | Prisma | 5.x | Type-safe queries, excellent migrations |
| Validation | Zod | 3.x | Schema validation with TypeScript inference |
| Auth | JWT + bcrypt | - | Stateless authentication, secure password hashing |
| Database | PostgreSQL | 15 | Robust, full-text search, JSON support |
| Cache | Redis | 7.x | Fast in-memory storage, rate limiting |
| Frontend | Vanilla JS | ES2022 | No framework overhead, smaller bundle |
| Build Tool | Vite | 5.x | Fast HMR, optimized production builds |
| Container | Docker | - | Consistent environments, portable |
| Cloud | Azure | - | Enterprise features, good Node.js support |

---

## Architecture Decision Records

### ADR-001: Architecture Style - Modular Monolith

**Status**: Accepted

**Context**: We need to choose an architecture style that balances development velocity, operational simplicity, and future scalability.

**Decision**: We will use a Modular Monolith architecture.

**Consequences**:
- (+) Simpler deployment and operations
- (+) Easier testing and debugging
- (+) Faster initial development
- (+) Strong data consistency
- (-) Limited independent scalability of components
- (-) Technology stack lock-in per module
- (-) Requires discipline to maintain module boundaries

---

*Document Version: 1.0*
*Last Updated: 2024*
*Author: System Architect*
