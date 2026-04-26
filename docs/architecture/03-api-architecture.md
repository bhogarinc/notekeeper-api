# API Architecture

## NoteKeeper API Architecture Documentation

This document describes the REST API design, authentication flows, integration patterns, and rate limiting strategy.

---

## 1. API Design Principles

### 1.1 RESTful Design Standards

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     REST API DESIGN PRINCIPLES                               │
└─────────────────────────────────────────────────────────────────────────────┘

Resource-Based URLs:
  ✓ GET    /api/v1/notes           # Collection of notes
  ✓ GET    /api/v1/notes/:id       # Single note resource
  ✓ POST   /api/v1/notes           # Create new note
  ✓ PUT    /api/v1/notes/:id       # Full update
  ✓ PATCH  /api/v1/notes/:id       # Partial update
  ✓ DELETE /api/v1/notes/:id       # Delete note

HTTP Status Codes:
  200 OK           - Successful GET, PUT, PATCH
  201 Created      - Successful POST
  204 No Content   - Successful DELETE
  400 Bad Request  - Validation error
  401 Unauthorized - Missing/invalid authentication
  403 Forbidden    - Insufficient permissions
  404 Not Found    - Resource doesn't exist
  409 Conflict     - Resource conflict (e.g., duplicate)
  422 Unprocessable - Business logic error
  429 Too Many Requests - Rate limit exceeded
  500 Server Error - Unexpected server error

Response Format:
  {
    "success": boolean,
    "data": object | array | null,
    "error": {
      "code": string,
      "message": string,
      "details": object (optional)
    },
    "meta": {
      "page": number,
      "limit": number,
      "total": number,
      "totalPages": number
    } (for paginated responses)
  }
```

### 1.2 API Versioning Strategy

```
URL Path Versioning (Selected):
  /api/v1/notes
  /api/v2/notes

Rationale:
  - Clear and explicit
  - Easy to route at load balancer level
  - Cache-friendly
  - Self-documenting

Version Lifecycle:
  - v1: Current stable (minimum 12 months support)
  - v2: In development
  - Deprecation: 6 months notice with sunset headers
```

---

## 2. API Endpoints Specification

### 2.1 Authentication Endpoints

```yaml
openapi: 3.0.0
info:
  title: NoteKeeper API
  version: 1.0.0
paths:
  /api/v1/auth/register:
    post:
      summary: Register new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  minLength: 8
                displayName:
                  type: string
                  maxLength: 100
      responses:
        201:
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: object
                    properties:
                      user:
                        $ref: '#/components/schemas/User'
                      tokens:
                        $ref: '#/components/schemas/TokenPair'
        409:
          description: Email already exists

  /api/v1/auth/login:
    post:
      summary: Authenticate user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: object
                    properties:
                      user:
                        $ref: '#/components/schemas/User'
                      tokens:
                        $ref: '#/components/schemas/TokenPair'
        401:
          description: Invalid credentials

  /api/v1/auth/refresh:
    post:
      summary: Refresh access token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [refreshToken]
              properties:
                refreshToken:
                  type: string
      responses:
        200:
          description: New tokens issued
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/TokenPair'
        401:
          description: Invalid or expired refresh token

  /api/v1/auth/logout:
    post:
      summary: Logout user
      security:
        - BearerAuth: []
      responses:
        204:
          description: Logout successful

  /api/v1/auth/me:
    get:
      summary: Get current user profile
      security:
        - BearerAuth: []
      responses:
        200:
          description: User profile
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/User'
```

### 2.2 Notes Endpoints

```yaml
  /api/v1/notes:
    get:
      summary: List notes with filtering and pagination
      security:
        - BearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: categoryId
          in: query
          schema:
            type: string
            format: uuid
        - name: tagIds
          in: query
          schema:
            type: array
            items:
              type: string
        - name: isPinned
          in: query
          schema:
            type: boolean
        - name: isArchived
          in: query
          schema:
            type: boolean
            default: false
        - name: search
          in: query
          schema:
            type: string
        - name: sortBy
          in: query
          schema:
            type: string
            enum: [createdAt, updatedAt, title]
            default: updatedAt
        - name: sortOrder
          in: query
          schema:
            type: string
            enum: [asc, desc]
            default: desc
      responses:
        200:
          description: Paginated list of notes
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Note'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'

    post:
      summary: Create new note
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title:
                  type: string
                  maxLength: 255
                content:
                  type: string
                categoryId:
                  type: string
                  format: uuid
                tagIds:
                  type: array
                  items:
                    type: string
                    format: uuid
                isPinned:
                  type: boolean
                  default: false
      responses:
        201:
          description: Note created
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/Note'

  /api/v1/notes/{id}:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
          format: uuid

    get:
      summary: Get single note
      security:
        - BearerAuth: []
      responses:
        200:
          description: Note details
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/NoteDetail'
        404:
          description: Note not found

    put:
      summary: Update note (full replacement)
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NoteInput'
      responses:
        200:
          description: Note updated

    patch:
      summary: Update note (partial)
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NotePatch'
      responses:
        200:
          description: Note updated

    delete:
      summary: Delete note (soft delete)
      security:
        - BearerAuth: []
      responses:
        204:
          description: Note deleted

  /api/v1/notes/{id}/pin:
    patch:
      summary: Toggle pin status
      security:
        - BearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                isPinned:
                  type: boolean
      responses:
        200:
          description: Pin status updated

  /api/v1/notes/{id}/archive:
    patch:
      summary: Toggle archive status
      security:
        - BearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                isArchived:
                  type: boolean
      responses:
        200:
          description: Archive status updated
```

### 2.3 Search Endpoint

```yaml
  /api/v1/notes/search:
    get:
      summary: Full-text search notes
      security:
        - BearerAuth: []
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 2
            maxLength: 200
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        200:
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/NoteSearchResult'
                  meta:
                    type: object
                    properties:
                      total:
                        type: integer
                      query:
                        type: string
                      executionTimeMs:
                        type: number
```

### 2.4 Categories Endpoints

```yaml
  /api/v1/categories:
    get:
      summary: List all categories
      security:
        - BearerAuth: []
      responses:
        200:
          description: List of categories
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Category'

    post:
      summary: Create category
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name]
              properties:
                name:
                  type: string
                  maxLength: 100
                color:
                  type: string
                  pattern: '^#[0-9A-Fa-f]{6}$'
                icon:
                  type: string
                  maxLength: 50
      responses:
        201:
          description: Category created

  /api/v1/categories/{id}:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
          format: uuid

    put:
      summary: Update category
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CategoryInput'
      responses:
        200:
          description: Category updated

    delete:
      summary: Delete category
      security:
        - BearerAuth: []
      responses:
        204:
          description: Category deleted
```

### 2.5 Tags Endpoints

```yaml
  /api/v1/tags:
    get:
      summary: List all tags
      security:
        - BearerAuth: []
      parameters:
        - name: search
          in: query
          schema:
            type: string
      responses:
        200:
          description: List of tags

    post:
      summary: Create tag
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name]
              properties:
                name:
                  type: string
                  maxLength: 50
                color:
                  type: string
      responses:
        201:
          description: Tag created

  /api/v1/tags/{id}:
    delete:
      summary: Delete tag
      security:
        - BearerAuth: []
      responses:
        204:
          description: Tag deleted
```

### 2.6 Schema Definitions

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
        displayName:
          type: string
        createdAt:
          type: string
          format: date-time

    TokenPair:
      type: object
      properties:
        accessToken:
          type: string
        refreshToken:
          type: string
        expiresIn:
          type: integer
          description: Seconds until access token expires

    Note:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        content:
          type: string
        contentHtml:
          type: string
        isPinned:
          type: boolean
        isArchived:
          type: boolean
        category:
          $ref: '#/components/schemas/Category'
        tags:
          type: array
          items:
            $ref: '#/components/schemas/Tag'
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    NoteDetail:
      allOf:
        - $ref: '#/components/schemas/Note'
        - type: object
          properties:
            attachments:
              type: array
              items:
                $ref: '#/components/schemas/Attachment'

    Category:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        color:
          type: string
        icon:
          type: string
        noteCount:
          type: integer

    Tag:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        color:
          type: string
        noteCount:
          type: integer

    Attachment:
      type: object
      properties:
        id:
          type: string
          format: uuid
        filename:
          type: string
        originalName:
          type: string
        mimeType:
          type: string
        sizeBytes:
          type: integer
        url:
          type: string
        createdAt:
          type: string
          format: date-time

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        totalPages:
          type: integer
        hasNextPage:
          type: boolean
        hasPrevPage:
          type: boolean
```

---

## 3. Authentication Architecture

### 3.1 JWT Token Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JWT AUTHENTICATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐                              ┌─────────────┐
    │  Client │                              │    Server   │
    └────┬────┘                              └──────┬──────┘
         │                                          │
         │ 1. POST /auth/login                      │
         │    {email, password}                     │
         │─────────────────────────────────────────>│
         │                                          │
         │                                          │ 2. Validate credentials
         │                                          │    (bcrypt compare)
         │                                          │
         │                                          │ 3. Generate tokens
         │                                          │    - Access token (15min)
         │                                          │    - Refresh token (7 days)
         │                                          │
         │                                          │ 4. Store refresh token hash
         │                                          │    in database
         │                                          │
         │ 5. Return tokens                         │
         │<─────────────────────────────────────────│
         │    {accessToken, refreshToken}           │
         │                                          │
         │ 6. Store tokens                          │
         │    - Access: Memory (short-lived)        │
         │    - Refresh: httpOnly cookie            │
         │                                          │
         │ 7. API Request                           │
         │    Authorization: Bearer {accessToken}   │
         │─────────────────────────────────────────>│
         │                                          │
         │                                          │ 8. Verify JWT signature
         │                                          │    Check expiration
         │                                          │
         │ 9. Return data                           │
         │<─────────────────────────────────────────│
         │                                          │
         │ 10. Token expired (401)                  │
         │<─────────────────────────────────────────│
         │                                          │
         │ 11. POST /auth/refresh                   │
         │     {refreshToken}                       │
         │─────────────────────────────────────────>│
         │                                          │
         │                                          │ 12. Verify refresh token
         │                                          │     Check database
         │                                          │
         │                                          │ 13. Rotate refresh token
         │                                          │     (delete old, create new)
         │                                          │
         │ 14. New tokens                           │
         │<─────────────────────────────────────────│
```

### 3.2 Token Specifications

```typescript
// Token Configuration
const TokenConfig = {
  accessToken: {
    secret: process.env.JWT_ACCESS_SECRET!,
    expiresIn: '15m',
    algorithm: 'HS256' as const,
  },
  refreshToken: {
    secret: process.env.JWT_REFRESH_SECRET!,
    expiresIn: '7d',
    algorithm: 'HS256' as const,
  },
};

// Access Token Payload
interface AccessTokenPayload {
  sub: string;        // User ID
  email: string;      // User email
  type: 'access';
  iat: number;        // Issued at
  exp: number;        // Expiration
}

// Refresh Token Payload
interface RefreshTokenPayload {
  sub: string;        // User ID
  jti: string;        // Token ID (for rotation)
  type: 'refresh';
  iat: number;
  exp: number;
}
```

### 3.3 Security Considerations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION SECURITY                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Token Storage:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Access Token                                                       │
  │  - Stored in JavaScript memory (Redux/Zustand store)                │
  │  - NOT stored in localStorage (XSS protection)                      │
  │  - Short lifetime (15 minutes) minimizes exposure window            │
  ├─────────────────────────────────────────────────────────────────────┤
  │  Refresh Token                                                      │
  │  - Stored in httpOnly, secure, sameSite cookie                      │
  │  - Also stored hashed in database for revocation                    │
  │  - Longer lifetime (7 days) with rotation                           │
  └─────────────────────────────────────────────────────────────────────┘

Token Rotation:
  - Each refresh token use generates NEW refresh token
  - Old refresh token is invalidated (single use)
  - Prevents replay attacks if refresh token is stolen

Token Revocation:
  - User logout: Delete refresh token from database
  - Password change: Revoke all refresh tokens
  - Suspicious activity: Admin can revoke specific tokens

CSRF Protection:
  - SameSite=Strict cookie attribute
  - Double-submit cookie pattern for non-GET requests
  - CORS whitelist for API domain
```

---

## 4. Rate Limiting Strategy

### 4.1 Rate Limit Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RATE LIMITING TIERS                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Tier 1: Unauthenticated
  - Limit: 100 requests per hour per IP
  - Window: Sliding window (Redis)
  - Endpoints: /auth/*, health checks
  - Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

Tier 2: Authenticated - Standard
  - Limit: 1000 requests per hour per user
  - Window: Sliding window
  - Endpoints: All standard API operations
  - Burst: 100 requests per minute

Tier 3: Authenticated - Search
  - Limit: 60 requests per minute per user
  - Window: Fixed window
  - Endpoints: /api/v1/notes/search
  - Reason: Search is computationally expensive

Tier 4: Authenticated - Write Operations
  - Limit: 300 requests per hour per user
  - Window: Sliding window
  - Endpoints: POST, PUT, PATCH, DELETE
  - Reason: Prevent spam/abuse

Tier 5: Attachment Uploads
  - Limit: 50 requests per hour per user
  - Max file size: 10MB per file
  - Max total storage: 100MB per user
```

### 4.2 Rate Limit Implementation

```typescript
// Rate limiting middleware using Redis
import { Redis } from 'ioredis';

interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  keyPrefix: string;
}

class RateLimiter {
  private redis: Redis;

  constructor(redisUrl: string) {
    this.redis = new Redis(redisUrl);
  }

  async checkLimit(
    identifier: string,
    config: RateLimitConfig
  ): Promise<{
    allowed: boolean;
    remaining: number;
    resetTime: number;
    totalLimit: number;
  }> {
    const key = `${config.keyPrefix}:${identifier}`;
    const windowSeconds = Math.ceil(config.windowMs / 1000);
    
    // Use Redis INCR with EXPIRE for sliding window approximation
    const current = await this.redis.incr(key);
    
    if (current === 1) {
      // First request in window, set expiry
      await this.redis.expire(key, windowSeconds);
    }
    
    const ttl = await this.redis.ttl(key);
    const remaining = Math.max(0, config.maxRequests - current);
    const resetTime = Date.now() + (ttl * 1000);
    
    return {
      allowed: current <= config.maxRequests,
      remaining,
      resetTime,
      totalLimit: config.maxRequests,
    };
  }
}

// Express middleware
const rateLimitMiddleware = (config: RateLimitConfig) => {
  const limiter = new RateLimiter(process.env.REDIS_URL!);
  
  return async (req: Request, res: Response, next: NextFunction) => {
    const identifier = req.user?.id || req.ip;
    const result = await limiter.checkLimit(identifier, config);
    
    // Set rate limit headers
    res.set({
      'X-RateLimit-Limit': result.totalLimit.toString(),
      'X-RateLimit-Remaining': result.remaining.toString(),
      'X-RateLimit-Reset': new Date(result.resetTime).toISOString(),
    });
    
    if (!result.allowed) {
      return res.status(429).json({
        success: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests, please try again later',
          details: {
            retryAfter: Math.ceil((result.resetTime - Date.now()) / 1000),
          },
        },
      });
    }
    
    next();
  };
};

// Usage
app.use('/api/v1/notes/search', rateLimitMiddleware({
  windowMs: 60 * 1000, // 1 minute
  maxRequests: 60,
  keyPrefix: 'ratelimit:search',
}));
```

---

## 5. Error Handling

### 5.1 Error Response Structure

```typescript
// Standardized error response
interface ApiError {
  success: false;
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable message
    details?: Record<string, unknown>; // Additional context
    stack?: string;         // Only in development
  };
}

// Error code categories
enum ErrorCodes {
  // Validation errors (400)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_JSON = 'INVALID_JSON',
  MISSING_FIELD = 'MISSING_FIELD',
  INVALID_FORMAT = 'INVALID_FORMAT',
  
  // Authentication errors (401)
  UNAUTHORIZED = 'UNAUTHORIZED',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  INVALID_TOKEN = 'INVALID_TOKEN',
  
  // Authorization errors (403)
  FORBIDDEN = 'FORBIDDEN',
  INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',
  
  // Not found errors (404)
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  NOTE_NOT_FOUND = 'NOTE_NOT_FOUND',
  
  // Conflict errors (409)
  DUPLICATE_EMAIL = 'DUPLICATE_EMAIL',
  DUPLICATE_RESOURCE = 'DUPLICATE_RESOURCE',
  
  // Rate limit (429)
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // Server errors (500)
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',
}
```

### 5.2 Error Handling Middleware

```typescript
// Global error handler
const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  // Log error
  logger.error({
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.user?.id,
  });

  // Handle specific error types
  if (err instanceof ValidationError) {
    return res.status(400).json({
      success: false,
      error: {
        code: ErrorCodes.VALIDATION_ERROR,
        message: 'Validation failed',
        details: err.errors,
      },
    });
  }

  if (err instanceof UnauthorizedError) {
    return res.status(401).json({
      success: false,
      error: {
        code: ErrorCodes.UNAUTHORIZED,
        message: 'Authentication required',
      },
    });
  }

  if (err instanceof NotFoundError) {
    return res.status(404).json({
      success: false,
      error: {
        code: ErrorCodes.RESOURCE_NOT_FOUND,
        message: err.message,
      },
    });
  }

  // Default server error
  const isDev = process.env.NODE_ENV === 'development';
  
  return res.status(500).json({
    success: false,
    error: {
      code: ErrorCodes.INTERNAL_ERROR,
      message: 'An unexpected error occurred',
      ...(isDev && { stack: err.stack }),
    },
  });
};

// Apply middleware
app.use(errorHandler);
```

---

## 6. API Gateway Configuration

### 6.1 Azure Front Door Setup

```yaml
# Azure Front Door configuration
frontDoor:
  name: notekeeper-fd
  sku: Premium_AzureFrontDoor
  
  endpoints:
    - name: api-endpoint
      hostName: api.notekeeper.app
      
  originGroups:
    - name: api-origin-group
      loadBalancing:
        sampleSize: 4
        successfulSamplesRequired: 2
        additionalLatencyMilliseconds: 50
      healthProbe:
        protocol: HTTPS
        path: /health
        intervalSeconds: 30
      
  origins:
    - name: app-service-primary
      hostName: notekeeper-prod.azurewebsites.net
      httpPort: 80
      httpsPort: 443
      priority: 1
      weight: 100
      
  routes:
    - name: api-route
      endpoint: api-endpoint
      originGroup: api-origin-group
      patterns:
        - /api/*
      acceptedProtocols:
        - HTTPS
      forwardingProtocol: HTTPSOnly
      caching:
        enabled: true
        queryParameters: [page, limit, sortBy]
        
  rules:
    - name: security-headers
      actions:
        responseHeaders:
          - header: X-Content-Type-Options
            value: nosniff
          - header: X-Frame-Options
            value: DENY
          - header: Strict-Transport-Security
            value: max-age=31536000; includeSubDomains
```

---

*Document Version: 1.0*
*Last Updated: 2024*
*Author: System Architect*
