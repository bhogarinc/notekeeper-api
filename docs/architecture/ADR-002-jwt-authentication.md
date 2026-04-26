# ADR-002: JWT Authentication with RS256

## Status
Accepted

## Context
NoteKeeper requires stateless authentication for:
- REST API security
- SPA frontend integration
- Future mobile app support
- Horizontal scalability

## Decision
We will use **JWT (JSON Web Tokens)** with **RS256** (RSA with SHA-256) signing algorithm.

## Token Strategy

### Access Token
- **Expiry**: 15 minutes
- **Algorithm**: RS256
- **Payload**: userId, email, roles, iat, exp
- **Storage**: Memory only (SPA)

### Refresh Token
- **Expiry**: 7 days
- **Algorithm**: RS256
- **Storage**: Redis (server-side) + httpOnly cookie (client-side)
- **Rotation**: New refresh token issued on each use

## Rationale

### Why JWT?
1. **Stateless**: No server-side session storage needed
2. **Scalable**: Easy horizontal scaling
3. **Cross-domain**: Works across microservices if needed later
4. **Standard**: Industry-standard with broad library support

### Why RS256?
1. **Asymmetric**: Public key can be shared without compromising security
2. **Key Rotation**: Easier to rotate keys without affecting clients
3. **Verification**: Resource servers can verify without private key

### Why Short-lived Access Tokens?
1. **Security**: Limited window if token compromised
2. **Revocation**: Refresh token rotation enables revocation

## Implementation

### Token Generation
```javascript
// Access Token
jwt.sign(payload, privateKey, { algorithm: 'RS256', expiresIn: '15m' })

// Refresh Token
jwt.sign({ userId }, privateKey, { algorithm: 'RS256', expiresIn: '7d' })
```

### Token Validation
```javascript
jwt.verify(token, publicKey, { algorithms: ['RS256'] })
```

## Security Considerations

1. **Private Key**: Stored securely (Azure Key Vault)
2. **Token Storage**: Access token in memory, refresh in httpOnly cookie
3. **HTTPS Only**: All token transmissions over HTTPS
4. **Blacklist**: Refresh tokens can be revoked in Redis

## Date
April 26, 2026
