# NoteKeeper System Architecture - Overview

## 1. Architecture Overview

### 1.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL USERS                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Web App   │    │  Mobile App │    │  API Clients│                      │
│  │   Users     │    │    Users    │    │  (Third-Party)│                    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                      │
└─────────┼──────────────────┼──────────────────┼────────────────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTPS/REST
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NOTEKEEPER SYSTEM                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Azure Application Gateway                       │    │
│  │                   (SSL Termination, Rate Limiting)                   │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Azure App Service (Node.js)                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │    │
│  │  │   Static    │  │    API      │  │  Auth       │  │  Search    │ │    │
│  │  │   Assets    │  │   Server    │  │  Middleware │  │  Service   │ │    │
│  │  │  (SPA)      │  │  (Express)  │  │   (JWT)     │  │ (Full-Text)│ │    │
│  │  └─────────────┘  └──────┬──────┘  └─────────────┘  └────────────┘ │    │
│  │                          │                                         │    │
│  └──────────────────────────┼─────────────────────────────────────────┘    │
│                             │                                                │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Azure SQL     │  │  Azure Cache    │  │  Azure Blob     │
│   Database      │  │  for Redis      │  │   Storage       │
│  (Primary Data) │  │ (Session/Cache) │  │ (File Uploads)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 1.2 Architecture Style: Modular Monolith

**Selected Architecture: Modular Monolith with Clean Architecture Principles**

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Architecture Style** | Modular Monolith | Simpler deployment, lower operational overhead |
| **Scalability Strategy** | Horizontal scaling via Azure App Service | Auto-scaling based on CPU/memory metrics |
| **Data Consistency** | ACID transactions (SQL) | Note-taking requires strong consistency |
| **API Style** | RESTful JSON | Industry standard, excellent tooling support |
| **Authentication** | JWT with refresh tokens | Stateless, scalable, secure |

**Why Not Microservices?**
- Current scope doesn't justify operational complexity
- Single development team
- Lower latency requirements
- Simpler debugging and testing

**Future Migration Path:**
- Search Service → Azure Cognitive Search
- File Service → Dedicated microservice
- Notification Service → Event-driven architecture

---

## 2. Technology Stack Summary

### 2.1 Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TECHNOLOGY STACK                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND: Vanilla JavaScript (ES2022+), Custom CSS, Marked.js             │
│  BACKEND:  Node.js 20 LTS, Express.js 4.x, Sequelize 6.x                   │
│  DATABASE: Azure SQL Database, Azure Cache for Redis                       │
│  STORAGE:  Azure Blob Storage                                              │
│  CLOUD:    Microsoft Azure (App Service, Front Door, Key Vault)           │
│  CI/CD:    GitHub Actions                                                 │
│  MONITOR:  Azure Application Insights                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Dependencies

**Production:**
- `express` - Web framework
- `sequelize` - ORM
- `tedious` - SQL Server driver
- `jsonwebtoken` - JWT authentication
- `bcryptjs` - Password hashing
- `helmet` - Security headers
- `cors` - Cross-origin requests
- `express-rate-limit` - Rate limiting
- `winston` - Logging
- `joi` - Validation
- `marked` - Markdown parsing
- `dompurify` - XSS prevention
- `ioredis` - Redis client
- `@azure/storage-blob` - Azure Blob Storage

**Development:**
- `nodemon` - Auto-restart
- `jest` - Testing framework
- `eslint` - Linting
- `supertest` - HTTP testing
