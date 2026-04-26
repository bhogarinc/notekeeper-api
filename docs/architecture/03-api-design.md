# NoteKeeper API Design

## API Gateway Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Base URL: https://notekeeper-bhogarai.azurewebsites.net/api/v1             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Global Middleware (Applied to all routes)                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  1. Helmet          - Security headers                               │    │
│  │  2. CORS            - Cross-origin handling                          │    │
│  │  3. Compression     - Gzip compression                               │    │
│  │  4. Request ID      - UUID per request (tracing)                     │    │
│  │  5. Rate Limiter    - 100 req/min per IP                             │    │
│  │  6. Morgan Logger   - HTTP request logging                           │    │
│  │  7. Body Parser     - JSON parsing (10MB limit)                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Authentication Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/auth/register | Public | User registration |
| POST | /api/v1/auth/login | Public | User login |
| POST | /api/v1/auth/refresh | Public | Refresh access token |
| POST | /api/v1/auth/logout | Authenticated | Logout user |
| POST | /api/v1/auth/forgot-password | Public | Request password reset |
| POST | /api/v1/auth/reset-password | Public | Reset password with token |

### Notes Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/notes | Authenticated | List notes (paginated) |
| POST | /api/v1/notes | Authenticated | Create note |
| GET | /api/v1/notes/:id | Authenticated | Get single note |
| PUT | /api/v1/notes/:id | Authenticated | Update note |
| DELETE | /api/v1/notes/:id | Authenticated | Soft delete note |
| PATCH | /api/v1/notes/:id/pin | Authenticated | Toggle pin status |
| PATCH | /api/v1/notes/:id/archive | Authenticated | Toggle archive status |
| GET | /api/v1/notes/search | Authenticated | Full-text search |

### Categories Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/categories | Authenticated | List categories |
| POST | /api/v1/categories | Authenticated | Create category |
| PUT | /api/v1/categories/:id | Authenticated | Update category |
| DELETE | /api/v1/categories/:id | Authenticated | Delete category |

### Tags Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/tags | Authenticated | List tags |
| POST | /api/v1/tags | Authenticated | Create tag |
| PUT | /api/v1/tags/:id | Authenticated | Update tag |
| DELETE | /api/v1/tags/:id | Authenticated | Delete tag |
| GET | /api/v1/tags/popular | Authenticated | Most used tags |

### Attachments Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/v1/attachments | Authenticated | Upload file |
| DELETE | /api/v1/attachments/:id | Authenticated | Delete file |
| GET | /api/v1/attachments/:id/download | Authenticated | Download file |

### User Routes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/v1/user/profile | Authenticated | Get user profile |
| PUT | /api/v1/user/profile | Authenticated | Update profile |
| PUT | /api/v1/user/password | Authenticated | Change password |
| DELETE | /api/v1/user/account | Authenticated | Delete account |

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "My Note",
    "content": "# Hello World",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  },
  "requestId": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      { "field": "email", "message": "Email is required" }
    ]
  },
  "requestId": "550e8400-e29b-41d4-a716-446655440000"
}
```

## JWT Authentication Flow

```
┌─────────────┐                                    ┌─────────────┐
│    User     │                                    │    Auth     │
│   Client    │                                    │   Service   │
└──────┬──────┘                                    └──────┬──────┘
       │                                                  │
       │  1. POST /auth/login                             │
       │     { email, password }                          │
       │─────────────────────────────────────────────────►│
       │                                                  │
       │  2. Validate credentials                         │
       │                                                  │
       │  3. { accessToken, refreshToken, user }          │
       │◄─────────────────────────────────────────────────│
       │                                                  │
       │  4. Store tokens                                 │
       │                                                  │
       │══════════════════════════════════════════════════│
       │         SUBSEQUENT REQUESTS                      │
       │══════════════════════════════════════════════════│
       │                                                  │
       │  5. GET /api/notes                               │
       │     Authorization: Bearer {accessToken}          │
       │─────────────────────────────────────────────────►│
       │                                                  │
       │  6. Verify JWT signature                         │
       │                                                  │
       │  7. { notes: [...] }                             │
       │◄─────────────────────────────────────────────────│
       │                                                  │
       │══════════════════════════════════════════════════│
       │         TOKEN REFRESH (when 401)                 │
       │══════════════════════════════════════════════════│
       │                                                  │
       │  8. POST /auth/refresh                           │
       │     { refreshToken }                             │
       │─────────────────────────────────────────────────►│
       │                                                  │
       │  9. Validate & rotate token                      │
       │                                                  │
       │  10. { accessToken, refreshToken }               │
       │◄─────────────────────────────────────────────────│
```

## Token Specifications

### Access Token
```javascript
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "role": "user",
    "iat": 1704067200,
    "exp": 1704070800  // 1 hour
  }
}
```

### Refresh Token (Database)
```javascript
{
  "id": "refresh-token-uuid",
  "userId": "user-uuid",
  "tokenHash": "sha256-of-token",
  "expiresAt": "2024-02-01T00:00:00Z",  // 7 days
  "createdAt": "2024-01-25T00:00:00Z",
  "ipAddress": "192.168.1.1",
  "userAgent": "Mozilla/5.0..."
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing credentials |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
