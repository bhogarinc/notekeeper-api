# NoteKeeper Data Flow Documentation

## Overview
This document describes the data flow patterns for key operations in NoteKeeper.

## Authentication Flow

### Login Flow
```
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌────────┐
│ Client  │────▶│   API    │────▶│   Auth      │────▶│  DB    │
└─────────┘     │  Layer   │     │  Service    │     └────────┘
                └──────────┘     └─────────────┘          │
                     │                   │                  │
                     │                   │                  ▼
                     │                   │             Validate
                     │                   │             Password
                     │                   │                  │
                     │                   ▼                  │
                     │            Generate Tokens           │
                     │                   │                  │
                     ▼                   ▼                  │
               Return JWT          Store Refresh            │
               Tokens              in Redis                 │
```

### Authenticated Request Flow
```
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌────────┐
│ Client  │────▶│  JWT     │────▶│   Route     │────▶│Handler │
│(Bearer) │     │ Middleware│     │   Handler   │     └────────┘
└─────────┘     └──────────┘     └─────────────┘
                      │
                      ▼
               Verify Token
               Check Redis
               Blacklist
```

## Note CRUD Flows

### Create Note
```
Client          API Layer       Validation      Service         Database
  │                │                │              │                │
  │ POST /notes    │                │              │                │
  │───────────────▶│                │              │                │
  │                │ Validate JWT   │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Validate Body  │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Sanitize       │              │                │
  │                │ Markdown→HTML  │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Create Note    │              │                │
  │                │───────────────────────────────▶│                │
  │                │                │              │ Begin Transaction
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Insert Note     │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Link Tags       │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │◀───────────────│
  │                │                │              │ Commit          │
  │                │                │              │────────────────▶
  │                │◀──────────────────────────────│                │
  │                │                │              │                │
  │  201 Created   │                │              │                │
  │◀───────────────│                │              │                │
  │                │                │              │                │
  │                │ Invalidate Cache              │                │
  │                │───────────────────────────────▶│                │
```

### Search Notes (with Cache)
```
Client          API Layer       Cache Service     Search Service    Database
  │                │                │                │                │
  │ GET /search    │                │                │                │
  │───────────────▶│                │                │                │
  │                │ Check Cache    │                │                │
  │                │───────────────▶│                │                │
  │                │◀───────────────│                │                │
  │                │                │                │                │
  │                │ [Cache Miss]   │                │                │
  │                │                │                │                │
  │                │ Execute Search │                │                │
  │                │───────────────────────────────▶│                │
  │                │                │                │                │
  │                │                │                │ FTS Query       │
  │                │                │                │────────────────▶
  │                │                │                │                │
  │                │                │                │ Rank Results    │
  │                │                │                │◀───────────────│
  │                │                │                │                │
  │                │◀───────────────────────────────│                │
  │                │                │                │                │
  │                │ Store in Cache │                │                │
  │                │───────────────▶│                │                │
  │                │◀───────────────│                │                │
  │                │                │                │                │
  │  200 OK        │                │                │                │
  │◀───────────────│                │                │                │
```

## Category Management Flow

### Create Category
```
Client          API Layer       Validation      Service         Database
  │                │                │              │                │
  │ POST /cats     │                │              │                │
  │───────────────▶│                │              │                │
  │                │ Validate JWT   │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Validate Body  │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Check Duplicate│              │                │
  │                │───────────────────────────────▶│                │
  │                │◀───────────────────────────────│                │
  │                │                │              │                │
  │                │ Create Category│              │                │
  │                │───────────────────────────────▶│                │
  │                │                │              │ Insert          │
  │                │                │              │────────────────▶
  │                │◀───────────────────────────────│                │
  │                │                │              │                │
  │  201 Created   │                │              │                │
  │◀───────────────│                │              │                │
```

## Tag Management Flow

### Add Tags to Note
```
Client          API Layer       Validation      Service         Database
  │                │                │              │                │
  │ PUT /notes/:id │                │              │                │
  │ {tags: [...]}  │                │              │                │
  │───────────────▶│                │              │                │
  │                │ Validate JWT   │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Validate Tags  │              │                │
  │                │───────────────▶│              │                │
  │                │◀───────────────│              │                │
  │                │                │              │                │
  │                │ Update Tags    │              │                │
  │                │───────────────────────────────▶│                │
  │                │                │              │                │
  │                │                │              │ Transaction     │
  │                │                │              │ Begin           │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Remove Old Tags │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Create New Tags │
  │                │                │              │ (if needed)     │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Link New Tags   │
  │                │                │              │────────────────▶
  │                │                │              │                │
  │                │                │              │ Commit          │
  │                │                │              │────────────────▶
  │                │◀───────────────────────────────│                │
  │                │                │              │                │
  │  200 OK        │                │              │                │
  │◀───────────────│                │              │                │
```

## Error Handling Flow

### Global Error Handler
```
Route Handler → Service Layer → Database
      │              │              │
      │              │              │
      ▼              ▼              ▼
  [Error Thrown]
      │
      ▼
┌─────────────────────────────────────┐
│      Express Error Middleware       │
│  ┌───────────────────────────────┐  │
│  │  1. Log error with correlation│  │
│  │  2. Check error type          │  │
│  │  3. Sanitize for client       │  │
│  │  4. Send appropriate response │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
      │
      ▼
Client Response (JSON)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [...]
  }
}
```

## Cache Invalidation Strategy

### Cache Keys
| Key Pattern | TTL | Invalidation Trigger |
|------------|-----|---------------------|
| `notes:{userId}:list:{cursor}` | 2 min | Note create/update/delete |
| `notes:{userId}:{noteId}` | 5 min | Note update/delete |
| `search:{userId}:{query}` | 5 min | Any note change |
| `categories:{userId}` | 10 min | Category change |
| `tags:{userId}` | 10 min | Tag change |

### Invalidation Flow
```
Note Modified
      │
      ▼
┌─────────────────────┐
│  Cache Invalidator  │
│  ┌───────────────┐  │
│  │ 1. Delete     │  │
│  │    note:{id}  │  │
│  │ 2. Delete     │  │
│  │    notes:list │  │
│  │ 3. Delete     │  │
│  │    search:*   │  │
│  └───────────────┘  │
└─────────────────────┘
```

## Event Flow (Future)

### Potential Event-Driven Extensions
```
Note Created
      │
      ├──▶ Search Index Worker
      │
      ├──▶ Notification Service
      │
      └──▶ Analytics Pipeline
```

## Data Retention

### Soft Delete Pattern
All entities implement soft delete:
```javascript
{
  id: UUID,
  ...fields,
  deletedAt: DateTime?,  // null = active
  createdAt: DateTime,
  updatedAt: DateTime
}
```

### Cleanup Job
- Archived notes older than 1 year: Hard delete monthly
- Expired refresh tokens: Daily cleanup
- Old search cache: LRU eviction

---

*Last Updated: April 26, 2026*
