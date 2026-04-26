# ADR-001: Modular Monolith Architecture

## Status
Accepted

## Context
NoteKeeper is a note-taking application with the following characteristics:
- Small to medium-sized application with clear domain boundaries
- Single development team
- Need for rapid development and deployment
- Future scalability requirements uncertain

## Decision
We will implement a **Modular Monolith** architecture.

## Rationale

### Why Not Microservices?
1. **Operational Complexity**: Microservices require sophisticated DevOps, monitoring, and service discovery
2. **Network Overhead**: Inter-service communication adds latency
3. **Data Consistency**: Distributed transactions are complex to manage
4. **Team Size**: Single team can efficiently work on a monolith

### Why Modular Monolith?
1. **Simplicity**: Single deployment unit, easier testing
2. **Clear Boundaries**: Modules (Auth, Notes, Categories, Tags) are well-defined
3. **Future Flexibility**: Can extract services later if needed
4. **Performance**: No network calls between modules
5. **Transaction Safety**: ACID compliance within the database

## Consequences

### Positive
- Faster development cycles
- Easier debugging and testing
- Simpler deployment pipeline
- Lower infrastructure costs

### Negative
- Limited independent scaling of modules
- Technology stack lock-in
- Risk of tight coupling if boundaries not respected

## Module Boundaries

```
src/
├── modules/
│   ├── auth/          # Authentication & authorization
│   ├── notes/         # Note CRUD & search
│   ├── categories/    # Category management
│   └── tags/          # Tag management
├── shared/            # Cross-cutting concerns
└── infrastructure/    # Database, cache, external services
```

## Compliance
- Each module has its own routes, controllers, services
- No direct database access between modules
- Shared code only in `shared/` directory
- Module dependencies documented in architecture decision log

## Date
April 26, 2026
