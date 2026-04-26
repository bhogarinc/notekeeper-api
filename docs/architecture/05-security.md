# NoteKeeper Security Architecture

## Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: Network Security                                                   │
│  ├── Azure Front Door (DDoS protection, WAF)                                │
│  ├── HTTPS only (TLS 1.2+)                                                  │
│  ├── IP restrictions (optional)                                             │
│  └── Private endpoints for database                                         │
│                                                                              │
│  Layer 2: Application Security                                               │
│  ├── Helmet.js security headers                                             │
│  ├── CORS configuration                                                     │
│  ├── Rate limiting (express-rate-limit)                                     │
│  ├── Input validation (Joi/Celebrate)                                       │
│  ├── XSS protection (DOMPurify)                                             │
│  └── CSRF protection                                                        │
│                                                                              │
│  Layer 3: Authentication & Authorization                                     │
│  ├── JWT with short expiry (1 hour)                                         │
│  ├── Refresh token rotation                                                 │
│  ├── Password hashing (bcrypt, 12 rounds)                                   │
│  ├── Role-based access control (RBAC)                                       │
│  └── Session management                                                     │
│                                                                              │
│  Layer 4: Data Security                                                      │
│  ├── Encryption at rest (Azure TDE)                                         │
│  ├── Encryption in transit (TLS)                                            │
│  ├── Field-level encryption for sensitive data                              │
│  └── Secure key management (Azure Key Vault)                                │
│                                                                              │
│  Layer 5: Operational Security                                               │
│  ├── Secrets management                                                     │
│  ├── Audit logging                                                          │
│  ├── Regular dependency scanning                                            │
│  └── Automated security updates                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Headers (Helmet Configuration)

```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "blob:", "https:"],
      connectSrc: ["'self'", process.env.API_URL],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false,
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
```

## Authentication Flow

### JWT Implementation

```javascript
// Token Configuration
const ACCESS_TOKEN_EXPIRY = '1h';      // Short-lived
const REFRESH_TOKEN_EXPIRY = '7d';     // Longer-lived
const BCRYPT_ROUNDS = 12;              // Password hashing

// Token Payload Structure
const accessTokenPayload = {
  sub: user.id,           // User ID
  email: user.email,      // User email
  role: user.role,        // User role
  iat: Date.now() / 1000, // Issued at
  exp: expiryTime         // Expiration
};
```

### Password Security

- **Hashing Algorithm**: bcrypt
- **Salt Rounds**: 12 (computationally expensive)
- **Minimum Length**: 8 characters
- **Complexity Requirements**: 
  - At least 1 uppercase
  - At least 1 lowercase
  - At least 1 number
  - At least 1 special character

### Rate Limiting

```javascript
const rateLimit = require('express-rate-limit');

// General API rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

// Stricter for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 attempts per 15 minutes
  skipSuccessfulRequests: true
});

app.use('/api/', apiLimiter);
app.use('/api/auth/', authLimiter);
```

## Data Protection

### Encryption Standards

| Data Type | Encryption Method | Key Management |
|-----------|-------------------|----------------|
| Database | Azure TDE | Azure-managed keys |
| In Transit | TLS 1.2+ | Azure Front Door |
| Secrets | AES-256 | Azure Key Vault |
| Passwords | bcrypt | N/A (one-way hash) |

### Sensitive Data Handling

```javascript
// Data sanitization before response
const sanitizeUser = (user) => ({
  id: user.id,
  email: user.email,
  username: user.username,
  firstName: user.first_name,
  lastName: user.last_name,
  avatarUrl: user.avatar_url,
  createdAt: user.created_at,
  // Explicitly exclude: password_hash, refresh_tokens, internal IDs
});
```

## Input Validation

### Validation Schema (Joi)

```javascript
const Joi = require('joi');

// User registration validation
const registerSchema = Joi.object({
  email: Joi.string().email().required().max(255),
  username: Joi.string().alphanum().min(3).max(50).required(),
  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
    .required()
    .messages({
      'string.pattern.base': 'Password must contain uppercase, lowercase, number and special character'
    }),
  firstName: Joi.string().max(100).allow(''),
  lastName: Joi.string().max(100).allow('')
});

// Note creation validation
const noteSchema = Joi.object({
  title: Joi.string().required().max(255),
  content: Joi.string().allow('').max(100000),
  categoryId: Joi.string().uuid().allow(null),
  tags: Joi.array().items(Joi.string().uuid()).max(10),
  color: Joi.string().pattern(/^#[0-9A-Fa-f]{6}$/).allow(null),
  isPinned: Joi.boolean().default(false)
});
```

## XSS Prevention

```javascript
const createDOMPurify = require('dompurify');
const { JSDOM } = require('jsdom');

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

// Sanitize HTML content before storage/display
const sanitizeHtml = (dirty) => {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'],
    ALLOWED_ATTR: ['href', 'title', 'target']
  });
};
```

## Security Checklist

### Pre-Deployment

- [ ] All dependencies scanned for vulnerabilities (`npm audit`)
- [ ] Security headers configured (Helmet)
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection enabled
- [ ] CSRF tokens for state-changing operations
- [ ] Secrets stored in Azure Key Vault
- [ ] HTTPS enforced
- [ ] Security logging enabled

### Ongoing

- [ ] Weekly dependency updates
- [ ] Monthly security audits
- [ ] Quarterly penetration testing
- [ ] Log monitoring for suspicious activity
- [ ] Incident response plan tested
