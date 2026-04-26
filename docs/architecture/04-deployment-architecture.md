# Deployment Architecture

## NoteKeeper Deployment Architecture Documentation

This document describes the complete deployment architecture, infrastructure setup, CI/CD pipelines, and monitoring strategy.

---

## 1. Environment Strategy

### 1.1 Environment Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONMENT STRATEGY                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        DEVELOPMENT                                   │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Local Machine                                               │   │
    │  │  - Docker Compose (PostgreSQL + Redis)                       │   │
    │  │  - Node.js 20 with hot reload                                │   │
    │  │  - Local .env file                                           │   │
    │  │  - SQLite option for quick testing                           │   │
    │  │  - No SSL required                                           │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Git Push to develop
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        STAGING                                       │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Azure Resources                                             │   │
    │  │  - App Service (Standard S1)                                 │   │
    │  │  - PostgreSQL Basic (Single zone)                            │   │
    │  │  - Redis Cache C0 (Basic)                                    │   │
    │  │  - Blob Storage (LRS)                                        │   │
    │  │  - No CDN (direct access)                                    │   │
    │  │  - Auto-deploy on PR merge to develop                        │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ PR to main + Approval
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      PRODUCTION                                      │
    │  ┌─────────────────────────────────────────────────────────────┐   │
    │  │  Azure Resources                                             │   │
    │  │  - App Service (Premium P2V2)                                │   │
    │  │  - PostgreSQL GP (Zone redundant)                            │   │
    │  │  - Redis Cache C1 (Standard)                                 │   │
    │  │  - Blob Storage (GRS) + CDN                                  │   │
    │  │  - Front Door (Global load balancing)                        │   │
    │  │  - Application Insights (APM)                                │   │
    │  │  - Manual approval required for deployment                   │   │
    │  └─────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Environment Specifications

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **Purpose** | Local development | Integration testing | Live users |
| **Branch** | feature/* | develop | main |
| **Database** | PostgreSQL 15 (Docker) | Azure PostgreSQL Basic | Azure PostgreSQL GP |
| **Cache** | Redis 7 (Docker) | Azure Redis C0 | Azure Redis C1 |
| **Storage** | Local filesystem | Azure Blob LRS | Azure Blob GRS |
| **CDN** | None | None | Azure CDN |
| **SSL** | Optional | Required | Required |
| **Monitoring** | Console logs | Basic App Insights | Full APM + Alerts |
| **Backup** | None | 7 days | 35 days + Geo |
| **Cost** | $0 | ~$50/month | ~$200/month |

---

## 2. Infrastructure Architecture

### 2.1 Production Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PRODUCTION ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │    User     │
                                    └──────┬──────┘
                                           │ HTTPS
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AZURE FRONT DOOR                                        │
│  - Global load balancing                                                             │
│  - DDoS protection                                                                   │
│  - SSL termination                                                                   │
│  - Caching rules                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                          ▼                ▼                ▼
                   ┌────────────┐   ┌────────────┐   ┌────────────┐
                   │  Region 1  │   │  Region 2  │   │  Region 3  │
                   │  (Primary) │   │ (Standby)  │   │  (CDN POP) │
                   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
                         │                │                │
                         ▼                ▼                ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                      AZURE APP SERVICE (Premium)                             │
    │                                                                              │
    │  ┌───────────────────────────────────────────────────────────────────────┐  │
    │  │  Container Group                                                     │  │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
    │  │  │   Instance  │  │   Instance  │  │   Instance  │  (Auto-scaling)  │  │
    │  │  │     1       │  │     2       │  │     N       │                  │  │
    │  │  │  (Node.js)  │  │  (Node.js)  │  │  (Node.js)  │                  │  │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘                  │  │
    │  └───────────────────────────────────────────────────────────────────────┘  │
    │                                                                              │
    │  Health Checks: /health                                                      │
    │  Auto-scale: CPU > 70% for 10 min                                            │
    │                                                                              │
    └─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  Azure Database  │  │   Azure Cache    │  │  Azure Blob      │
    │  for PostgreSQL  │  │   for Redis      │  │   Storage        │
    │                  │  │                  │  │                  │
    │  - Zone redundant│  │  - Session store │  │  - Attachments   │
    │  - Private link  │  │  - Rate limiting │  │  - Backups       │
    │  - Read replicas │  │  - Query cache   │  │  - CDN origin    │
    └──────────────────┘  └──────────────────┘  └──────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                         SUPPORTING SERVICES                                  │
    │                                                                              │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
    │  │  Key Vault   │  │    CDN       │  │   Monitor    │  │    Log       │   │
    │  │   (Secrets)  │  │   (Static)   │  │   (Alerts)   │  │  Analytics   │   │
    │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
    └─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Azure Resource Organization

```yaml
# Resource Group Structure
resourceGroups:
  notekeeper-shared:
    description: Shared resources across environments
    resources:
      - Container Registry
      - Key Vault (shared secrets)
      
  notekeeper-dev:
    description: Development environment
    resources:
      - App Service (B1)
      - PostgreSQL (Basic)
      - Redis (C0)
      
  notekeeper-staging:
    description: Staging environment
    resources:
      - App Service (S1)
      - PostgreSQL (Basic)
      - Redis (C0)
      - Blob Storage (LRS)
      
  notekeeper-production:
    description: Production environment
    resources:
      - App Service Plan (Premium P2V2)
      - App Service (3 instances)
      - PostgreSQL (General Purpose, Zone redundant)
      - Redis (C1)
      - Blob Storage (GRS)
      - CDN Profile
      - Front Door
      - Application Insights
      - Log Analytics Workspace
```

---

## 3. Container Architecture

### 3.1 Dockerfile

```dockerfile
# Multi-stage Dockerfile for NoteKeeper API
# Stage 1: Dependencies
FROM node:20-alpine AS dependencies
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from previous stage
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .

# Generate Prisma Client
RUN npx prisma generate

# Build TypeScript
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS production
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy production dependencies
COPY --from=dependencies --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/prisma ./prisma
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

# Start application
CMD ["node", "dist/index.js"]
```

### 3.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/notekeeper?schema=public
      - REDIS_URL=redis://redis:6379
      - JWT_ACCESS_SECRET=dev-access-secret
      - JWT_REFRESH_SECRET=dev-refresh-secret
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./uploads:/app/uploads
    networks:
      - notekeeper-network

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=notekeeper
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - notekeeper-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - notekeeper-network

  # Optional: Admin tools
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@notekeeper.local
      - PGADMIN_DEFAULT_PASSWORD=admin
    ports:
      - "5050:80"
    depends_on:
      - db
    networks:
      - notekeeper-network

volumes:
  postgres-data:
  redis-data:

networks:
  notekeeper-network:
    driver: bridge
```

---

## 4. CI/CD Pipeline

### 4.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  NODE_VERSION: '20'
  AZURE_WEBAPP_NAME: notekeeper-bhogarai

jobs:
  # ============================================
  # Job 1: Test & Lint
  # ============================================
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: notekeeper_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Generate Prisma Client
        run: npx prisma generate

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npm run type-check

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/notekeeper_test?schema=public
          REDIS_URL: redis://localhost:6379
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  # ============================================
  # Job 2: Build & Push Docker Image
  # ============================================
  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Azure Container Registry
        uses: azure/docker-login@v1
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.ACR_LOGIN_SERVER }}/notekeeper:${{ github.sha }}
            ${{ secrets.ACR_LOGIN_SERVER }}/notekeeper:${{ github.ref_name }}
            ${{ secrets.ACR_LOGIN_SERVER }}/notekeeper:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # Job 3: Deploy to Staging
  # ============================================
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://notekeeper-staging.azurewebsites.net

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Staging
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}-staging
          images: ${{ secrets.ACR_LOGIN_SERVER }}/notekeeper:${{ github.sha }}

      - name: Run database migrations
        run: |
          az webapp ssh --name ${{ env.AZURE_WEBAPP_NAME }}-staging \
            --resource-group notekeeper-staging \
            --command "npx prisma migrate deploy"

      - name: Health check
        run: |
          sleep 30
          curl -f https://${{ env.AZURE_WEBAPP_NAME }}-staging.azurewebsites.net/health || exit 1

  # ============================================
  # Job 4: Deploy to Production
  # ============================================
  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://notekeeper.app

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Production (Blue-Green)
        run: |
          # Determine which slot to deploy to
          CURRENT_SLOT=$(az webapp deployment slot list \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group notekeeper-production \
            --query "[?name!='production'].[name,state]" -o tsv | grep "Running" | head -1 | cut -f1)
          
          TARGET_SLOT=$([ "$CURRENT_SLOT" == "staging" ] && echo "staging2" || echo "staging")
          
          # Deploy to target slot
          az webapp config container set \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group notekeeper-production \
            --slot $TARGET_SLOT \
            --docker-custom-image-name ${{ secrets.ACR_LOGIN_SERVER }}/notekeeper:${{ github.sha }}
          
          # Run migrations on target slot
          az webapp ssh --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group notekeeper-production \
            --slot $TARGET_SLOT \
            --command "npx prisma migrate deploy"
          
          # Warm up slot
          curl -f https://${{ env.AZURE_WEBAPP_NAME }}-$TARGET_SLOT.azurewebsites.net/health
          
          # Swap slots
          az webapp deployment slot swap \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group notekeeper-production \
            --slot $TARGET_SLOT \
            --target-slot production

      - name: Verify deployment
        run: |
          sleep 10
          curl -f https://notekeeper.app/health || exit 1

      - name: Notify on success
        if: success()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Production deployment successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*NoteKeeper* deployed to production\nCommit: ${{ github.sha }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: Rollback on failure
        if: failure()
        run: |
          az webapp deployment slot swap \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group notekeeper-production \
            --slot production \
            --target-slot $TARGET_SLOT
          
          # Notify of rollback
          echo "Deployment failed - rolled back to previous version"
```

---

## 5. Monitoring and Observability

### 5.1 Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │ Application │
    │   (Node.js) │
    └──────┬──────┘
           │ Logs, Metrics, Traces
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                  Azure Application Insights                          │
    │  ┌───────────────┬───────────────┬─────────────────────────────┐   │
    │  │   Traces      │   Metrics     │      Logs                   │   │
    │  │  (Requests)   │  (CPU/Memory) │   (Structured)              │   │
    │  └───────────────┴───────────────┴─────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    Azure Log Analytics                               │
    │  - Log aggregation and querying                                      │
    │  - Custom dashboards                                                 │
    │  - Alert rules                                                       │
    └─────────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         Alerts                                       │
    │  ┌───────────────┬───────────────┬─────────────────────────────┐   │
    │  │   Email       │   Slack       │      PagerDuty              │   │
    │  │   (Low)       │  (Medium)     │      (Critical)             │   │
    │  └───────────────┴───────────────┴─────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Metrics

| Category | Metric | Threshold | Alert |
|----------|--------|-----------|-------|
| **Availability** | Request success rate | < 99.9% | Critical |
| **Performance** | Response time (p95) | > 500ms | Warning |
| **Performance** | Response time (p99) | > 1000ms | Critical |
| **Errors** | 5xx error rate | > 1% | Critical |
| **Errors** | 4xx error rate | > 10% | Warning |
| **Resources** | CPU utilization | > 80% | Warning |
| **Resources** | Memory utilization | > 85% | Warning |
| **Database** | Connection pool usage | > 80% | Warning |
| **Database** | Query duration (p95) | > 100ms | Warning |
| **Business** | Failed logins | > 10/min | Warning |

### 5.3 Logging Standards

```typescript
// Structured logging configuration
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'notekeeper-api',
    version: process.env.APP_VERSION,
    environment: process.env.NODE_ENV,
  },
  transports: [
    new winston.transports.Console(),
  ],
});

// Request logging middleware
const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    
    logger.info('HTTP Request', {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      durationMs: duration,
      userId: req.user?.id,
      ip: req.ip,
      userAgent: req.get('user-agent'),
      requestId: req.id,
    });
  });
  
  next();
};

// Error logging
const logError = (error: Error, context: Record<string, unknown>) => {
  logger.error({
    message: error.message,
    stack: error.stack,
    ...context,
  });
};
```

### 5.4 Health Checks

```typescript
// Health check endpoints
import { Router } from 'express';
import { PrismaClient } from '@prisma/client';
import Redis from 'ioredis';

const prisma = new PrismaClient();
const redis = new Redis(process.env.REDIS_URL!);

const healthRouter = Router();

// Basic health check
healthRouter.get('/health', async (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.APP_VERSION,
  });
});

// Detailed health check with dependencies
healthRouter.get('/health/detailed', async (req, res) => {
  const checks = {
    database: { status: 'unknown', responseTime: 0 },
    cache: { status: 'unknown', responseTime: 0 },
  };
  
  // Check database
  try {
    const dbStart = Date.now();
    await prisma.$queryRaw`SELECT 1`;
    checks.database = {
      status: 'healthy',
      responseTime: Date.now() - dbStart,
    };
  } catch (error) {
    checks.database.status = 'unhealthy';
  }
  
  // Check Redis
  try {
    const cacheStart = Date.now();
    await redis.ping();
    checks.cache = {
      status: 'healthy',
      responseTime: Date.now() - cacheStart,
    };
  } catch (error) {
    checks.cache.status = 'unhealthy';
  }
  
  const isHealthy = Object.values(checks).every(c => c.status === 'healthy');
  
  res.status(isHealthy ? 200 : 503).json({
    status: isHealthy ? 'healthy' : 'unhealthy',
    timestamp: new Date().toISOString(),
    checks,
  });
});

// Readiness probe (for Kubernetes-style deployments)
healthRouter.get('/ready', async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    await redis.ping();
    res.status(200).send('Ready');
  } catch {
    res.status(503).send('Not Ready');
  }
});

// Liveness probe
healthRouter.get('/live', (req, res) => {
  res.status(200).send('Alive');
});

export { healthRouter };
```

---

## 6. Security Configuration

### 6.1 Security Headers

```typescript
// Security middleware
import helmet from 'helmet';
import cors from 'cors';

// Helmet configuration
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "blob:"],
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
    preload: true,
  },
}));

// CORS configuration
const corsOptions = {
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://notekeeper.app', 'https://www.notekeeper.app']
    : ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
};

app.use(cors(corsOptions));
```

### 6.2 Secrets Management

```yaml
# Azure Key Vault secrets structure
secrets:
  # Database
  database-url:
    description: PostgreSQL connection string
    
  # Redis
  redis-url:
    description: Redis connection string
    
  # JWT
  jwt-access-secret:
    description: JWT access token secret
    rotation: 90 days
    
  jwt-refresh-secret:
    description: JWT refresh token secret
    rotation: 90 days
    
  # Azure
  storage-connection-string:
    description: Azure Blob Storage connection
    
  # External Services
  sendgrid-api-key:
    description: Email service API key
    
  slack-webhook-url:
    description: Slack notifications webhook
```

---

*Document Version: 1.0*
*Last Updated: 2024*
*Author: System Architect*
