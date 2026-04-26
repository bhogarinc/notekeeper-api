# NoteKeeper Technology Decisions (ADRs)

## ADR-001: Architecture Style - Modular Monolith

### Status
Accepted

### Context
We need to choose an architecture style that balances simplicity, performance, and future scalability for the NoteKeeper note-taking API.

### Decision
We will use a **Modular Monolith** architecture with clear module boundaries.

### Consequences

**Positive:**
- Simpler deployment and operations
- Better performance (no network calls between modules)
- ACID transactions across modules
- Easier testing and debugging
- Lower infrastructure costs

**Negative:**
- Modules are tightly coupled at the database level
- Scaling requires scaling the entire application
- Technology stack is uniform across all modules

### Mitigation
- Clear module boundaries with well-defined interfaces
- Repository pattern for data access abstraction
- Event-driven internal communication for loose coupling
- Documented module APIs for future extraction

---

## ADR-002: Backend Framework - FastAPI

### Status
Accepted

### Context
We need a Python web framework that provides high performance, automatic API documentation, and modern async support.

### Decision
We will use **FastAPI** as our web framework.

### Alternatives Considered
- Django REST Framework: Too heavy, synchronous by default
- Flask: Requires more boilerplate, no native async
- Starlette: Too low-level, FastAPI builds on it

### Consequences

**Positive:**
- Native async/await support
- Automatic OpenAPI/Swagger documentation
- Built-in data validation with Pydantic
- Type hints for better IDE support
- Excellent performance (on par with Node.js/Go)

**Negative:**
- Smaller ecosystem than Django/Flask
- Relatively newer framework

---

## ADR-003: Database - PostgreSQL

### Status
Accepted

### Context
We need a relational database that supports full-text search, JSON operations, and has good Python integration.

### Decision
We will use **PostgreSQL 15+** as our primary database.

### Alternatives Considered
- MySQL: Less advanced full-text search, JSON support
- MongoDB: Would require separate search solution
- SQLite: Not suitable for production web applications

### Consequences

**Positive:**
- Native full-text search with GIN indexes
- JSONB support for flexible metadata
- ACID compliance
- Excellent Python/SQLAlchemy support
- Managed service available on Azure

**Negative:**
- Vertical scaling limits
- Complex horizontal sharding

---

## ADR-004: ORM - SQLAlchemy 2.0

### Status
Accepted

### Context
We need an ORM that supports async operations, type hints, and modern Python patterns.

### Decision
We will use **SQLAlchemy 2.0** with async support.

### Alternatives Considered
- Django ORM: Tied to Django framework
- Tortoise ORM: Less mature, smaller community
- Prisma Client Python: Newer, different paradigm

### Consequences

**Positive:**
- Native async support (asyncpg backend)
- Excellent type hint integration
- Mature ecosystem and community
- Flexible query building
- Alembic for migrations

**Negative:**
- Steep learning curve
- Verbose for simple operations

---

## ADR-005: Authentication - JWT with Refresh Tokens

### Status
Accepted

### Context
We need a stateless authentication mechanism that works well with REST APIs and SPAs.

### Decision
We will use **JWT access tokens** with **refresh token rotation**.

### Token Strategy
- Access tokens: 15-minute expiry, stored in memory
- Refresh tokens: 7-day expiry, HTTP-only cookies

### Alternatives Considered
- Session cookies: Less suitable for SPAs, CSRF concerns
- OAuth2: Overkill for single application
- API Keys: Not suitable for user authentication

### Consequences

**Positive:**
- Stateless authentication
- Works across multiple domains
- Easy to implement logout (token revocation)
- Refresh token rotation improves security

**Negative:**
- Token size overhead
- Cannot revoke access tokens instantly
- Requires secure token storage on client

---

## ADR-006: Frontend - React with TypeScript

### Status
Accepted

### Context
We need a modern frontend stack that provides type safety and a rich ecosystem.

### Decision
We will use **React 18** with **TypeScript**.

### Alternatives Considered
- Vue.js: Good alternative, smaller ecosystem
- Angular: Too heavy for this project
- Svelte: Interesting, but smaller community

### Consequences

**Positive:**
- Large ecosystem and community
- Excellent TypeScript support
- Component-based architecture
- Strong developer tools

**Negative:**
- Requires build tooling
- Can be complex for simple UIs

---

## ADR-007: UI Framework - Tailwind CSS

### Status
Accepted

### Context
We need a CSS framework that provides flexibility without locking us into a specific component library.

### Decision
We will use **Tailwind CSS** for styling.

### Alternatives Considered
- Bootstrap: Too opinionated, dated look
- Material-UI: Heavy dependency, Material Design look
- Chakra UI: Good alternative, more component-based

### Consequences

**Positive:**
- Utility-first approach
- Highly customizable
- Small bundle size with PurgeCSS
- No predefined component styles

**Negative:**
- HTML can become verbose
- Learning curve for utility classes

---

## ADR-008: Cache - Redis

### Status
Accepted

### Context
We need a caching layer for session storage, rate limiting, and query result caching.

### Decision
We will use **Redis** for caching.

### Alternatives Considered
- Memcached: Less features, no persistence
- In-memory cache: Doesn't work with multiple instances
- Azure Cache: Same as Redis, managed service

### Consequences

**Positive:**
- Rich data structures
- TTL support
- Pub/sub capabilities (future use)
- Managed service on Azure

**Negative:**
- Additional infrastructure to manage
- Data consistency concerns

---

## ADR-009: Deployment - Azure App Service

### Status
Accepted

### Context
We need a managed platform for deploying our Python application with minimal operational overhead.

### Decision
We will use **Azure App Service** with Docker containers.

### Alternatives Considered
- Azure Container Instances: Less features, no auto-scaling
- Azure Kubernetes Service: Overkill for this project
- AWS Elastic Beanstalk: Not Azure

### Consequences

**Positive:**
- Managed platform
- Built-in auto-scaling
- Easy deployment from GitHub
- SSL/HTTPS out of the box
- Built-in monitoring

**Negative:**
- Vendor lock-in
- Less control than IaaS

---

## ADR-010: CI/CD - GitHub Actions

### Status
Accepted

### Context
We need a CI/CD pipeline that integrates well with our GitHub repository.

### Decision
We will use **GitHub Actions** for CI/CD.

### Alternatives Considered
- Azure DevOps: Separate service, more complex
- Jenkins: Self-hosted, more maintenance
- Travis CI: Less integrated with GitHub

### Consequences

**Positive:**
- Native GitHub integration
- Free for public repositories
- Large marketplace of actions
- YAML-based configuration

**Negative:**
- Limited free minutes for private repos
- Less feature-rich than Azure DevOps

---

## ADR-011: Search Implementation - PostgreSQL Full-Text Search

### Status
Accepted

### Context
We need full-text search functionality for notes. We must choose between native PostgreSQL search or a dedicated search engine.

### Decision
We will use **PostgreSQL's native full-text search** with GIN indexes.

### Alternatives Considered
- Elasticsearch: More powerful, but additional infrastructure
- Azure Cognitive Search: Managed service, additional cost
- Meilisearch: Good alternative, but additional service

### Consequences

**Positive:**
- No additional infrastructure
- ACID compliance with data
- Can use SQL for complex queries
- Lower operational complexity

**Negative:**
- Less powerful than dedicated search engines
- May not scale as well for very large datasets
- Limited advanced search features

### Migration Path
If search requirements grow beyond PostgreSQL capabilities, we can:
1. Add Elasticsearch/Azure Cognitive Search
2. Use PostgreSQL as source of truth
3. Sync data to search index via change data capture

---

## ADR-012: API Versioning - URL Path Versioning

### Status
Accepted

### Context
We need a strategy for API versioning to allow future changes without breaking existing clients.

### Decision
We will use **URL path versioning** (`/api/v1/...`).

### Alternatives Considered
- Header versioning: Less visible, harder to test
- Query parameter versioning: Pollutes URL
- Content negotiation: Complex for clients

### Consequences

**Positive:**
- Clear and explicit
- Easy to route in FastAPI
- Simple to test (just change URL)
- Industry standard approach

**Negative:**
- URL changes with versions
- Multiple versions to maintain

---

## ADR-013: State Management - Zustand

### Status
Accepted

### Context
We need a state management solution for the React frontend that is lightweight and TypeScript-friendly.

### Decision
We will use **Zustand** for state management.

### Alternatives Considered
- Redux: Too verbose for this project
- React Context: Performance issues with frequent updates
- Jotai: Good alternative, similar to Zustand

### Consequences

**Positive:**
- Minimal boilerplate
- Excellent TypeScript support
- Small bundle size (~1KB)
- No providers needed

**Negative:**
- Smaller ecosystem than Redux
- Less debugging tools

---

## ADR-014: Documentation - OpenAPI + Confluence

### Status
Accepted

### Context
We need to maintain both technical API documentation and high-level architecture documentation.

### Decision
- **OpenAPI/Swagger**: Auto-generated from FastAPI for API docs
- **Confluence**: Architecture documentation and decision records

### Alternatives Considered
- Postman: Good for testing, less for documentation
- Markdown in repo: Good for developers, less accessible
- Notion: Good alternative to Confluence

### Consequences

**Positive:**
- OpenAPI is always up-to-date
- Interactive API documentation
- Confluence for broader audience

**Negative:**
- Two documentation systems to maintain
- Confluence is proprietary

---

*Document Version: 1.0*
*Last Updated: 2024-01-02*
