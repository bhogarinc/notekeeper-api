# NoteKeeper Database Schema

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE SCHEMA (ERD)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐        │
│   │    users     │         │   categories │         │     tags     │        │
│   ├──────────────┤         ├──────────────┤         ├──────────────┤        │
│   │ PK id        │◄────────┤ PK id        │         │ PK id        │        │
│   │    uuid      │    1:M  │ FK user_id   │         │ FK user_id   │◄───────┤
│   │    email     │         │    name      │         │    name      │   M:M  │
│   │    password  │         │    color     │         │    color     │        │
│   │    username  │         │    icon      │         │    created_at│        │
│   │    created_at│         │    created_at│         │              │        │
│   │    updated_at│         │    updated_at│         │              │        │
│   └──────┬───────┘         └──────────────┘         └───────┬──────┘        │
│          │                                                   │              │
│          │ 1:M                                               │              │
│          ▼                                                   │              │
│   ┌──────────────┐         ┌──────────────┐                  │              │
│   │    notes     │         │ note_tags    │──────────────────┘              │
│   ├──────────────┤         │ (junction)   │                                 │
│   │ PK id        │◄────────┤ PK note_id   │                                 │
│   │ FK user_id   │    1:M  │ PK tag_id    │                                 │
│   │ FK category_id         └──────────────┘                                 │
│   │    title     │                                                          │
│   │    content   │         ┌──────────────┐                                 │
│   │    is_pinned │         │ attachments  │                                 │
│   │    is_archived        ├──────────────┤                                 │
│   │    color     │◄────────┤ PK id        │                                 │
│   │    created_at│    1:M  │ FK note_id   │                                 │
│   │    updated_at│         │    filename  │                                 │
│   │    deleted_at│         │    url       │                                 │
│   │ (soft delete)│         │    size      │                                 │
│   └──────────────┘         │    mime_type │                                 │
│                            │    created_at│                                 │
│                            └──────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## SQL Schema Definition

```sql
-- ============================================
-- NOTEKEEPER DATABASE SCHEMA
-- Azure SQL Database Compatible
-- ============================================

-- Users Table
CREATE TABLE users (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    email NVARCHAR(255) NOT NULL UNIQUE,
    username NVARCHAR(50) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    avatar_url NVARCHAR(500),
    is_active BIT DEFAULT 1,
    email_verified BIT DEFAULT 0,
    last_login_at DATETIME2,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);

-- Categories Table
CREATE TABLE categories (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    color NVARCHAR(7) DEFAULT '#6366f1',
    icon NVARCHAR(50) DEFAULT 'folder',
    sort_order INT DEFAULT 0,
    is_default BIT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT FK_categories_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- Tags Table
CREATE TABLE tags (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    name NVARCHAR(50) NOT NULL,
    color NVARCHAR(7) DEFAULT '#8b5cf6',
    usage_count INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT FK_tags_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT UQ_tags_user_name UNIQUE(user_id, name)
);

-- Notes Table
CREATE TABLE notes (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    category_id UNIQUEIDENTIFIER,
    title NVARCHAR(255) NOT NULL,
    content NVARCHAR(MAX),
    content_plain NVARCHAR(MAX),
    is_pinned BIT DEFAULT 0,
    is_archived BIT DEFAULT 0,
    color NVARCHAR(7),
    word_count INT DEFAULT 0,
    character_count INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    deleted_at DATETIME2 NULL,
    
    CONSTRAINT FK_notes_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT FK_notes_category FOREIGN KEY (category_id) 
        REFERENCES categories(id) ON DELETE SET NULL
);

-- Note-Tags Junction Table
CREATE TABLE note_tags (
    note_id UNIQUEIDENTIFIER NOT NULL,
    tag_id UNIQUEIDENTIFIER NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    
    PRIMARY KEY (note_id, tag_id),
    CONSTRAINT FK_notetags_note FOREIGN KEY (note_id) 
        REFERENCES notes(id) ON DELETE CASCADE,
    CONSTRAINT FK_notetags_tag FOREIGN KEY (tag_id) 
        REFERENCES tags(id) ON DELETE CASCADE
);

-- Attachments Table
CREATE TABLE attachments (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    note_id UNIQUEIDENTIFIER NOT NULL,
    user_id UNIQUEIDENTIFIER NOT NULL,
    filename NVARCHAR(255) NOT NULL,
    original_name NVARCHAR(255) NOT NULL,
    url NVARCHAR(500) NOT NULL,
    size_bytes BIGINT NOT NULL,
    mime_type NVARCHAR(100) NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT FK_attachments_note FOREIGN KEY (note_id) 
        REFERENCES notes(id) ON DELETE CASCADE,
    CONSTRAINT FK_attachments_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- Refresh Tokens Table
CREATE TABLE refresh_tokens (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    token_hash NVARCHAR(255) NOT NULL,
    expires_at DATETIME2 NOT NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    revoked_at DATETIME2 NULL,
    replaced_by_token UNIQUEIDENTIFIER NULL,
    ip_address NVARCHAR(45),
    user_agent NVARCHAR(500),
    
    CONSTRAINT FK_refreshtokens_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX IX_notes_user_created ON notes(user_id, created_at DESC);
CREATE INDEX IX_notes_user_pinned ON notes(user_id, is_pinned DESC, updated_at DESC);
CREATE INDEX IX_notes_user_archived ON notes(user_id, is_archived, updated_at DESC);
CREATE INDEX IX_notes_category ON notes(category_id);
CREATE INDEX IX_notes_deleted_at ON notes(deleted_at) WHERE deleted_at IS NOT NULL;

CREATE INDEX IX_categories_user ON categories(user_id, sort_order);
CREATE INDEX IX_tags_user ON tags(user_id, name);
CREATE INDEX IX_attachments_note ON attachments(note_id);
CREATE INDEX IX_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IX_refresh_tokens_token ON refresh_tokens(token_hash);

-- Full-Text Search
CREATE FULLTEXT CATALOG NoteKeeperCatalog AS DEFAULT;
CREATE FULLTEXT INDEX ON notes(title, content_plain)
    KEY INDEX PK__notes__3213E83F;
```

## Caching Strategy

| Cache Type | TTL | Use Case | Key Pattern |
|------------|-----|----------|-------------|
| **Session** | 24h | User authentication | `session:{userId}` |
| **Note List** | 5m | Paginated note lists | `notes:list:{userId}:{page}:{limit}` |
| **Note Detail** | 10m | Individual note data | `note:{noteId}` |
| **Search Results** | 2m | Full-text search | `search:{userId}:{query_hash}` |
| **Categories** | 15m | User categories | `categories:{userId}` |
| **Tags** | 15m | User tags | `tags:{userId}` |
| **Rate Limit** | 15m | API rate limiting | `ratelimit:{ip}:{endpoint}` |
