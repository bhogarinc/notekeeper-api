# NoteKeeper API Design Specification

## 1. API Overview

### 1.1 Base URL
```
Production:  https://notekeeper.app/api/v1
Staging:     https://staging.notekeeper.app/api/v1
Local:       http://localhost:8000/api/v1
```

### 1.2 Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### 1.3 Standard Response Format

**Success Response (200-299):**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**List Response with Pagination:**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**Error Response (400-599):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## 2. Authentication Endpoints

### 2.1 Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    },
    "message": "Registration successful. Please verify your email."
  }
}
```

### 2.2 Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

### 2.3 Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

### 2.4 Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

### 2.5 Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-01-15T10:30:00Z",
    "last_login_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## 3. Notes Endpoints

### 3.1 List Notes
```http
GET /notes?page=1&per_page=20&sort_by=updated_at&order=desc&status=active&search=query&category_id=uuid&tag_ids=uuid1,uuid2&is_pinned=true
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| per_page | integer | 20 | Items per page (max 100) |
| sort_by | string | updated_at | updated_at, created_at, title |
| order | string | desc | asc, desc |
| status | string | active | active, archived, all |
| search | string | - | Full-text search query |
| category_id | uuid | - | Filter by category |
| tag_ids | string | - | Comma-separated tag IDs |
| is_pinned | boolean | - | Filter by pinned status |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "My Note",
      "summary": "Auto-generated summary...",
      "is_pinned": true,
      "is_archived": false,
      "color": "#3b82f6",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "categories": [{"id": "uuid", "name": "Work", "color": "#3b82f6"}],
      "tags": [{"id": "uuid", "name": "important", "color": "#ef4444"}],
      "attachment_count": 2
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "has_next": true
  }
}
```

### 3.2 Create Note
```http
POST /notes
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "My New Note",
  "content": "# Heading\n\nNote content in markdown...",
  "is_pinned": false,
  "color": "#ffffff",
  "category_ids": ["uuid1", "uuid2"],
  "tag_ids": ["uuid3"]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "My New Note",
    "content": "# Heading\n\nNote content in markdown...",
    "summary": "Auto-generated summary...",
    "is_pinned": false,
    "is_archived": false,
    "color": "#ffffff",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "categories": [],
    "tags": []
  }
}
```

### 3.3 Get Note
```http
GET /notes/{note_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "My Note",
    "content": "Full markdown content...",
    "summary": "Auto-generated summary...",
    "is_pinned": true,
    "is_archived": false,
    "color": "#3b82f6",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "categories": [...],
    "tags": [...],
    "attachments": [
      {
        "id": "uuid",
        "filename": "document.pdf",
        "original_name": "My Document.pdf",
        "mime_type": "application/pdf",
        "file_size": 1024000,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### 3.4 Update Note
```http
PATCH /notes/{note_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content...",
  "is_pinned": true,
  "color": "#10b981",
  "category_ids": ["uuid1"],
  "tag_ids": ["uuid2", "uuid3"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Updated Title",
    "content": "Updated content...",
    "summary": "Updated summary...",
    "is_pinned": true,
    "color": "#10b981",
    "updated_at": "2024-01-15T11:00:00Z",
    "categories": [...],
    "tags": [...]
  }
}
```

### 3.5 Delete Note (Soft Delete)
```http
DELETE /notes/{note_id}
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

### 3.6 Archive Note
```http
POST /notes/{note_id}/archive
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "is_archived": true,
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### 3.7 Unarchive Note
```http
POST /notes/{note_id}/unarchive
Authorization: Bearer <access_token>
```

### 3.8 Pin Note
```http
POST /notes/{note_id}/pin
Authorization: Bearer <access_token>
```

### 3.9 Unpin Note
```http
POST /notes/{note_id}/unpin
Authorization: Bearer <access_token>
```

### 3.10 Bulk Operations
```http
POST /notes/bulk/archive
POST /notes/bulk/delete
POST /notes/bulk/restore
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "note_ids": ["uuid1", "uuid2", "uuid3"]
}
```

---

## 4. Categories Endpoints

### 4.1 List Categories
```http
GET /categories
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Work",
      "color": "#3b82f6",
      "icon": "briefcase",
      "sort_order": 1,
      "note_count": 25,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 4.2 Create Category
```http
POST /categories
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Personal",
  "color": "#10b981",
  "icon": "user",
  "sort_order": 2
}
```

### 4.3 Update Category
```http
PATCH /categories/{category_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Personal Life",
  "color": "#8b5cf6"
}
```

### 4.4 Delete Category
```http
DELETE /categories/{category_id}
Authorization: Bearer <access_token>
```

---

## 5. Tags Endpoints

### 5.1 List Tags
```http
GET /tags
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "important",
      "color": "#ef4444",
      "note_count": 10
    }
  ]
}
```

### 5.2 Create Tag
```http
POST /tags
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "urgent",
  "color": "#f59e0b"
}
```

### 5.3 Update Tag
```http
PATCH /tags/{tag_id}
Authorization: Bearer <access_token>
```

### 5.4 Delete Tag
```http
DELETE /tags/{tag_id}
Authorization: Bearer <access_token>
```

---

## 6. Attachments Endpoints

### 6.1 Upload Attachment
```http
POST /notes/{note_id}/attachments
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary data>
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "filename": "document_abc123.pdf",
    "original_name": "My Document.pdf",
    "mime_type": "application/pdf",
    "file_size": 1024000,
    "download_url": "/api/v1/attachments/uuid/download",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 6.2 Download Attachment
```http
GET /attachments/{attachment_id}/download
Authorization: Bearer <access_token>
```

**Response:** Binary file with appropriate Content-Type and Content-Disposition headers.

### 6.3 Delete Attachment
```http
DELETE /attachments/{attachment_id}
Authorization: Bearer <access_token>
```

---

## 7. Search Endpoints

### 7.1 Full-Text Search
```http
GET /search?q=meeting+notes&filters=category:work,tag:important
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notes": [...],
    "suggestions": ["meeting notes", "meeting minutes"],
    "total": 15
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "query": "meeting notes",
    "execution_time_ms": 45
  }
}
```

---

## 8. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Authentication required or failed |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict (duplicate, etc.) |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |

---

## 9. Rate Limiting

| Endpoint Group | Limit | Window |
|----------------|-------|--------|
| Authentication | 5 requests | 1 minute |
| General API | 100 requests | 1 minute |
| Search | 30 requests | 1 minute |
| File Upload | 10 requests | 1 minute |

Rate limit headers included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315800
```

---

*API Version: 1.0*
*Last Updated: System Architecture Phase*
