# Data Architecture

## NoteKeeper Data Architecture Documentation

This document describes the data architecture, database schema, caching strategy, and data flow for the NoteKeeper application.

---

## 1. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY RELATIONSHIP DIAGRAM                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │      User       │         │    Category     │         │       Tag       │
    ├─────────────────┤         ├─────────────────┤         ├─────────────────┤
    │ PK id (UUID)    │         │ PK id (UUID)    │         │ PK id (UUID)    │
    │    email        │         │ FK user_id      │◄────────│ FK user_id      │
    │    password_hash│         │    name         │         │    name         │
    │    display_name │         │    color        │         │    color        │
    │    created_at   │         │    icon         │         │    created_at   │
    │    updated_at   │         │    created_at   │         └─────────────────┘
    └────────┬────────┘         └────────┬────────┘                │
             │                           │                        │
             │ 1:N                       │ 1:N                    │ M:N
             │                           │                        │
             ▼                           ▼                        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                               Note                                      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │ PK id (UUID)                                                            │
    │ FK user_id ───────────────────────────────┐                             │
    │ FK category_id ───────────────────────────┤                             │
    │    title                                                                  │
    │    content (Markdown)                                                     │
    │    content_html (Generated)                                               │
    │    is_pinned (Boolean)                                                    │
    │    is_archived (Boolean)                                                  │
    │    metadata (JSONB)                                                       │
    │    search_vector (tsvector)                                               │
    │    created_at                                                             │
    │    updated_at                                                             │
    │    deleted_at (Soft Delete)                                               │
    └─────────────────────────────────────────────────────────────────────────┘
             │
             │ 1:N
             │
             ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          NoteTag (Join Table)                           │
    ├─────────────────────────────────────────────────────────────────────────┤
    │ PK id (UUID)                                                            │
    │ FK note_id                                                              │
    │ FK tag_id                                                               │
    │    created_at                                                           │
    └─────────────────────────────────────────────────────────────────────────┘
             │
             │ N:1
             ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                            Attachment                                   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │ PK id (UUID)                                                            │
    │ FK note_id                                                              │
    │    filename                                                             │
    │    original_name                                                        │
    │    mime_type                                                            │
    │    size_bytes                                                           │
    │    storage_path (Azure Blob)                                            │
    │    created_at                                                           │
    └─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         RefreshToken                                    │
    ├─────────────────────────────────────────────────────────────────────────┤
    │ PK id (UUID)                                                            │
    │ FK user_id                                                              │
    │    token_hash                                                           │
    │    expires_at                                                           │
    │    created_at                                                           │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema (Prisma)

```prisma
// schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============================================
// User Model
// ============================================
model User {
  id            String    @id @default(uuid()) @db.Uuid
  email         String    @unique @db.VarChar(255)
  passwordHash  String    @map("password_hash") @db.VarChar(255)
  displayName   String?   @map("display_name") @db.VarChar(100)
  
  // Timestamps
  createdAt     DateTime  @default(now()) @map("created_at") @db.Timestamptz(6)
  updatedAt     DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)
  
  // Relations
  notes         Note[]
  categories    Category[]
  tags          Tag[]
  refreshTokens RefreshToken[]
  
  @@index([email])
  @@map("users")
}

// ============================================
// Category Model
// ============================================
model Category {
  id          String   @id @default(uuid()) @db.Uuid
  userId      String   @map("user_id") @db.Uuid
  name        String   @db.VarChar(100)
  color       String?  @db.VarChar(7)  // Hex color code
  icon        String?  @db.VarChar(50)  // Icon name/identifier
  
  createdAt   DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  
  // Relations
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  notes       Note[]
  
  @@unique([userId, name])
  @@index([userId])
  @@map("categories")
}

// ============================================
// Tag Model
// ============================================
model Tag {
  id          String   @id @default(uuid()) @db.Uuid
  userId      String   @map("user_id") @db.Uuid
  name        String   @db.VarChar(50)
  color       String?  @db.VarChar(7)
  
  createdAt   DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  
  // Relations
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  noteTags    NoteTag[]
  
  @@unique([userId, name])
  @@index([userId])
  @@map("tags")
}

// ============================================
// Note Model
// ============================================
model Note {
  id            String    @id @default(uuid()) @db.Uuid
  userId        String    @map("user_id") @db.Uuid
  categoryId    String?   @map("category_id") @db.Uuid
  
  // Content
  title         String    @db.VarChar(255)
  content       String    @db.Text  // Markdown content
  contentHtml   String?   @map("content_html") @db.Text  // Pre-rendered HTML
  
  // Status
  isPinned      Boolean   @default(false) @map("is_pinned")
  isArchived    Boolean   @default(false) @map("is_archived")
  deletedAt     DateTime? @map("deleted_at") @db.Timestamptz(6)
  
  // Metadata
  metadata      Json?     @db.JsonB  // Flexible metadata storage
  
  // Full-text search
  searchVector  Unsupported("tsvector")? @map("search_vector")
  
  // Timestamps
  createdAt     DateTime  @default(now()) @map("created_at") @db.Timestamptz(6)
  updatedAt     DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)
  
  // Relations
  user          User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  category      Category? @relation(fields: [categoryId], references: [id], onDelete: SetNull)
  noteTags      NoteTag[]
  attachments   Attachment[]
  
  @@index([userId])
  @@index([userId, isArchived])
  @@index([userId, isPinned])
  @@index([userId, categoryId])
  @@index([deletedAt])
  @@index([searchVector], type: Gin)  // GIN index for full-text search
  @@map("notes")
}

// ============================================
// NoteTag Join Table
// ============================================
model NoteTag {
  id        String   @id @default(uuid()) @db.Uuid
  noteId    String   @map("note_id") @db.Uuid
  tagId     String   @map("tag_id") @db.Uuid
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  
  // Relations
  note      Note     @relation(fields: [noteId], references: [id], onDelete: Cascade)
  tag       Tag      @relation(fields: [tagId], references: [id], onDelete: Cascade)
  
  @@unique([noteId, tagId])
  @@index([noteId])
  @@index([tagId])
  @@map("note_tags")
}

// ============================================
// Attachment Model
// ============================================
model Attachment {
  id            String   @id @default(uuid()) @db.Uuid
  noteId        String   @map("note_id") @db.Uuid
  
  filename      String   @db.VarChar(255)
  originalName  String   @map("original_name") @db.VarChar(255)
  mimeType      String   @map("mime_type") @db.VarChar(100)
  sizeBytes     Int      @map("size_bytes")
  storagePath   String   @map("storage_path") @db.VarChar(500)  // Azure Blob path
  
  createdAt     DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  
  // Relations
  note          Note     @relation(fields: [noteId], references: [id], onDelete: Cascade)
  
  @@index([noteId])
  @@map("attachments")
}

// ============================================
// RefreshToken Model
// ============================================
model RefreshToken {
  id          String   @id @default(uuid()) @db.Uuid
  userId      String   @map("user_id") @db.Uuid
  tokenHash   String   @unique @map("token_hash") @db.VarChar(255)
  expiresAt   DateTime @map("expires_at") @db.Timestamptz(6)
  createdAt   DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  
  // Relations
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId])
  @@index([expiresAt])
  @@map("refresh_tokens")
}
```

---

## 3. Data Flow Diagrams

### 3.1 Note Creation Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Client  │────►│   Express   │────►│ Zod Validate │────►│ Auth Check   │
│  POST   │     │   Handler   │     │   Input      │     │   JWT        │
│ /notes  │     │             │     │              │     │              │
└─────────┘     └─────────────┘     └──────────────┘     └──────────────┘
                                                              │
                                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐  ┌──────────────┐
│   Client    │◄────│   Generate   │◄────│   Prisma     │◄─│   Process    │
│  Response   │     │   Search     │     │   Create     │  │   Content    │
│   201       │     │   Vector     │     │   Note       │  │ (Markdown)   │
└─────────────┘     └──────────────┘     └──────────────┘  └──────────────┘
                                                              │
                                                              ▼
                                                       ┌──────────────┐
                                                       │  PostgreSQL  │
                                                       │   Insert     │
                                                       └──────────────┘
```

### 3.2 Search Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Client  │────►│   Express   │────►│   Parse      │────►│  Check       │
│  GET    │     │   Handler   │     │   Query      │     │  Cache       │
│ /search │     │             │     │   Params     │     │  (Redis)     │
└─────────┘     └─────────────┘     └──────────────┘     └──────────────┘
                                                              │
                                    Cache Hit ────────────────┤
                                    (Return Cached)           │
                                                              │ Cache Miss
                                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐  ┌──────────────┐
│   Client    │◄────│    Cache     │◄────│   Format     │◄─│   Execute    │
│  Response   │     │    Store     │     │   Results    │  │   Search     │
│   200       │     │   (Redis)    │     │              │  │   Query      │
└─────────────┘     └──────────────┘     └──────────────┘  └──────────────┘
                                                              │
                                                              ▼
                                                       ┌──────────────┐
                                                       │  PostgreSQL  │
                                                       │ Full-Text    │
                                                       │   Search     │
                                                       └──────────────┘
```

### 3.3 Note Update with Tags Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Client  │────►│   Express   │────►│   Validate   │────►│  Fetch       │
│   PUT   │     │   Handler   │     │   Request    │     │  Existing    │
│ /notes  │     │             │     │              │     │  Note        │
│  /:id   │     │             │     │              │     │              │
└─────────┘     └─────────────┘     └──────────────┘     └──────────────┘
                                                              │
                                                              ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐  ┌──────────────┐
│   Client    │◄────│   Update     │◄────│   Process    │◄─│  Transaction │
│  Response   │     │   Search     │     │   Tags       │  │   Begin      │
│   200       │     │   Vector     │     │   (Sync)     │  │              │
└─────────────┘     └──────────────┘     └──────────────┘  └──────────────┘
                                                              │
           ┌──────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                     Tag Processing                               │
    │  1. Identify tags to add/remove                                 │
    │  2. Create new tags if needed                                   │
    │  3. Delete NoteTag associations                                 │
    │  4. Create new NoteTag associations                             │
    │  5. Update note content                                         │
    └─────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Transaction Commit                            │
    │  - Update note record                                           │
    │  - Sync tags (delete + insert)                                  │
    │  - Update search vector                                         │
    │  - Invalidate cache                                             │
    └─────────────────────────────────────────────────────────────────┘
```

---

## 4. Caching Strategy

### 4.1 Cache Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CACHING ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         Client Cache                                 │
    │  - Browser localStorage (user preferences, auth tokens)             │
    │  - Memory cache (React Query/SWR equivalent)                        │
    │  - Service Worker (offline support)                                 │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      CDN Cache (Azure CDN)                           │
    │  - Static assets (JS, CSS, images)                                  │
    │  - Cache-Control: public, max-age=31536000                          │
    │  - Immutable assets with content hash                               │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    Application Cache (Redis)                         │
    │  ┌───────────────┬───────────────┬─────────────────────────────┐   │
    │  │   Session     │   Query       │      Rate Limiting          │   │
    │  │   Store       │   Results     │                             │   │
    │  │  (1 hour)     │  (5 minutes)  │      (Sliding Window)       │   │
    │  └───────────────┴───────────────┴─────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Redis Cache Key Patterns

```typescript
// Cache key naming conventions
const CacheKeys = {
  // User sessions
  userSession: (userId: string) => `session:${userId}`,
  
  // Query results
  noteList: (userId: string, filters: string) => `notes:list:${userId}:${hash(filters)}`,
  noteDetail: (noteId: string) => `notes:detail:${noteId}`,
  categoryList: (userId: string) => `categories:list:${userId}`,
  tagList: (userId: string) => `tags:list:${userId}`,
  
  // Search results
  searchResults: (userId: string, query: string) => `search:${userId}:${hash(query)}`,
  
  // Rate limiting
  rateLimit: (identifier: string) => `ratelimit:${identifier}`,
  
  // Cache invalidation patterns
  userInvalidate: (userId: string) => `invalidate:user:${userId}`,
};

// TTL Configuration (seconds)
const CacheTTL = {
  session: 60 * 60,           // 1 hour
  noteList: 5 * 60,           // 5 minutes
  noteDetail: 10 * 60,        // 10 minutes
  searchResults: 2 * 60,      // 2 minutes
  categoryList: 15 * 60,      // 15 minutes
  tagList: 15 * 60,           // 15 minutes
  rateLimit: 60 * 60,         // 1 hour window
};
```

### 4.3 Cache Invalidation Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CACHE INVALIDATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Event: Note Created/Updated/Deleted
                │
                ▼
    ┌─────────────────────┐
    │  Invalidate User's  │
    │  Note List Cache    │
    └─────────────────────┘
                │
                ▼
    ┌─────────────────────┐
    │  Invalidate Note    │
    │  Detail Cache       │
    └─────────────────────┘
                │
                ▼
    ┌─────────────────────┐
    │  Invalidate Search  │
    │  Cache (wildcard)   │
    └─────────────────────┘
                │
                ▼
    ┌─────────────────────┐
    │  Invalidate Related │
    │  Category/Tag Lists │
    └─────────────────────┘
```

---

## 5. Data Migration Approach

### 5.1 Migration Strategy

We use Prisma Migrate for database schema migrations with the following workflow:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Developer  │────►│  Modify      │────►│  Generate    │────►│   Review     │
│   Change    │     │  Schema      │     │  Migration   │     │   Migration  │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Apply to  │◄────│   Deploy     │◄────│  CI/CD       │◄────│  Commit to   │
│ Production  │     │   to Staging │     │  Pipeline    │     │  Repository  │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 5.2 Migration Commands

```bash
# Development workflow
# 1. Modify schema.prisma
# 2. Generate migration
npx prisma migrate dev --name add_note_search_vector

# 3. Apply to production (CI/CD)
npx prisma migrate deploy

# 4. Generate Prisma Client
npx prisma generate

# 5. Verify migration status
npx prisma migrate status
```

### 5.3 Migration Safety Rules

1. **Never modify existing migrations** - Create new migrations for fixes
2. **Always have rollback plan** - Test downgrade path
3. **Avoid destructive changes** in production without data migration scripts
4. **Use transactions** for complex multi-step migrations
5. **Run migrations before code deployment** to maintain backward compatibility

### 5.4 Seeding Strategy

```typescript
// prisma/seed.ts
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  // Create default categories
  const defaultCategories = [
    { name: 'Personal', color: '#3B82F6', icon: 'user' },
    { name: 'Work', color: '#10B981', icon: 'briefcase' },
    { name: 'Ideas', color: '#F59E0B', icon: 'lightbulb' },
    { name: 'Learning', color: '#8B5CF6', icon: 'book' },
  ];

  // Create demo user
  const hashedPassword = await bcrypt.hash('demo123', 12);
  const demoUser = await prisma.user.create({
    data: {
      email: 'demo@notekeeper.app',
      passwordHash: hashedPassword,
      displayName: 'Demo User',
      categories: {
        create: defaultCategories,
      },
    },
  });

  console.log('Seed completed:', { demoUser });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

---

## 6. Backup and Disaster Recovery

### 6.1 Backup Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKUP ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                    Azure Database for PostgreSQL                     │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Automated Backups                                          │   │
    │  │  - Full backups: Daily                                      │   │
    │  │  - Differential: Every 4 hours                              │   │
    │  │  - Transaction logs: Continuous                             │   │
    │  │  - Retention: 35 days                                       │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Geo-Redundant Backup (Production)                          │   │
    │  │  - Replicated to paired region                              │   │
    │  │  - Point-in-time restore capability                         │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    Azure Blob Storage                                │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Attachment Backups                                         │   │
    │  │  - Azure Blob versioning enabled                            │   │
    │  │  - Soft delete: 30 days                                     │   │
    │  │  - Geo-redundancy: GRS (Geo-Redundant Storage)              │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Recovery Objectives

| Environment | RPO (Recovery Point) | RTO (Recovery Time) | Strategy |
|-------------|---------------------|---------------------|----------|
| Development | 24 hours | 4 hours | Restore from automated backup |
| Staging | 12 hours | 2 hours | Point-in-time restore |
| Production | 1 hour | 1 hour | Geo-restore + transaction replay |

### 6.3 Disaster Recovery Runbook

```markdown
# Disaster Recovery Runbook

## Scenario 1: Database Corruption

1. **Stop application** to prevent further corruption
   ```bash
   az webapp stop --name notekeeper-prod --resource-group notekeeper-rg
   ```

2. **Identify restore point** (last known good state)
   ```bash
   az postgres flexible-server list-backups \
     --name notekeeper-db-prod \
     --resource-group notekeeper-rg
   ```

3. **Restore database** to new instance
   ```bash
   az postgres flexible-server restore \
     --name notekeeper-db-recovery \
     --resource-group notekeeper-rg \
     --source-server notekeeper-db-prod \
     --restore-time "2024-01-15T10:30:00Z"
   ```

4. **Update connection string** and restart app
   ```bash
   az webapp config appsettings set \
     --name notekeeper-prod \
     --resource-group notekeeper-rg \
     --settings DATABASE_URL="new-connection-string"
   
   az webapp start --name notekeeper-prod --resource-group notekeeper-rg
   ```

## Scenario 2: Region Outage

1. **Initiate geo-failover** (if using geo-replication)
2. **Update DNS** to point to secondary region
3. **Verify application** functionality
4. **Monitor** for data consistency

## Post-Recovery
- Document incident timeline
- Verify data integrity
- Update runbook with lessons learned
```

---

## 7. Data Security

### 7.1 Encryption

| Layer | Method | Implementation |
|-------|--------|----------------|
| Data at Rest | AES-256 | Azure-managed keys for PostgreSQL and Blob Storage |
| Data in Transit | TLS 1.3 | Enforced HTTPS for all connections |
| Application Level | Field-level encryption | Optional for sensitive note content |
| Backups | AES-256 | Azure-managed encryption |

### 7.2 Access Control

```sql
-- Row Level Security (RLS) policies
-- Enable RLS on tables
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- Create policy for notes
CREATE POLICY user_notes_isolation ON notes
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::UUID);

-- Application sets user context before queries
SET app.current_user_id = 'user-uuid-here';
```

### 7.3 Data Retention

| Data Type | Retention Period | Action After Retention |
|-----------|-----------------|------------------------|
| Active Notes | Indefinite | None |
| Deleted Notes (Soft Delete) | 30 days | Hard delete |
| Session Data | 7 days | Automatic cleanup |
| Audit Logs | 1 year | Archive to cold storage |
| Expired Refresh Tokens | Immediate | Automatic cleanup |

---

*Document Version: 1.0*
*Last Updated: 2024*
*Author: System Architect*
