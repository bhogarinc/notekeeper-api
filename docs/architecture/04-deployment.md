# NoteKeeper Deployment Architecture

## Environment Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONMENT STRATEGY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DEVELOPMENT (Local)                                                 │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Local Node.js server (nodemon)                                   │    │
│  │  • SQLite or Local SQL Server (Docker)                              │    │
│  │  • Local Redis (Docker)                                             │    │
│  │  • Hot reload enabled                                               │    │
│  │  • Verbose logging                                                  │    │
│  │  • URL: http://localhost:3000                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ git push to develop branch              │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGING (Azure App Service - Staging Slot)                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Azure App Service (Linux, B1 tier)                               │    │
│  │  • Azure SQL Database (Basic tier)                                  │    │
│  │  • Azure Cache for Redis (C0 tier)                                  │    │
│  │  • Azure Blob Storage (standard)                                    │    │
│  │  • Application Insights enabled                                     │    │
│  │  • URL: https://notekeeper-staging.azurewebsites.net                │    │
│  │  • Auto-deploy from develop branch                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ PR + Code Review + Merge to main        │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PRODUCTION (Azure App Service - Production Slot)                    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Azure App Service (Linux, P1v2 tier or higher)                   │    │
│  │  • Azure SQL Database (Standard S2 or higher)                       │    │
│  │  • Azure Cache for Redis (C1 tier or higher)                        │    │
│  │  • Azure Blob Storage (with CDN)                                    │    │
│  │  • Azure Front Door (CDN + WAF)                                     │    │
│  │  • Application Insights + Alerts                                    │    │
│  │  • URL: https://notekeeper-bhogarai.azurewebsites.net               │    │
│  │  • Manual or gated deployment from main branch                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Azure Resource Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AZURE RESOURCE ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Resource Group: rg-notekeeper-prod (Central US)                     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Azure App Service Plan: asp-notekeeper-prod                 │   │    │
│  │  │  • OS: Linux                                                 │   │    │
│  │  │  • Tier: Premium V2 P1v2                                     │   │    │
│  │  │  • Instances: 2 (auto-scaling 2-5)                           │   │    │
│  │  │                                                              │   │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │   │    │
│  │  │  │  Web App: notekeeper-bhogarai                        │    │   │    │
│  │  │  │  • Runtime: Node.js 20                               │    │   │    │
│  │  │  │  • Deployment: GitHub Actions                        │    │   │    │
│  │  │  │  • HTTPS Only: Enabled                               │    │   │    │
│  │  │  │  • Min TLS: 1.2                                      │    │   │    │
│  │  │  └─────────────────────────────────────────────────────┘    │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Azure SQL Server: sql-notekeeper-prod                       │   │    │
│  │  │  • Version: 12.0                                             │   │    │
│  │  │  • Compute: Serverless (Gen5, 2 vCores)                      │   │    │
│  │  │  • Backup: Geo-redundant                                     │   │    │
│  │  │  • TDE: Enabled                                              │   │    │
│  │  │                                                              │   │    │
│  │  │  Database: sqldb-notekeeper-prod                             │   │    │
│  │  │  • Tier: Standard S2                                         │   │    │
│  │  │  • Max Size: 250 GB                                          │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Azure Cache for Redis: redis-notekeeper-prod                │   │    │
│  │  │  • Tier: Standard C1                                         │   │    │
│  │  │  • Memory: 1 GB                                              │   │    │
│  │  │  • SSL: Enabled                                              │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Storage Account: stnotekeeperprod                           │   │    │
│  │  │  • Tier: Standard (LRS)                                      │   │    │
│  │  │  • Containers: attachments (private), static (public)        │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Application Insights: appi-notekeeper-prod                  │   │    │
│  │  │  • Log Level: Warning (Production)                           │   │    │
│  │  │  • Sampling: Adaptive                                        │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │  │  Key Vault: kv-notekeeper-prod                               │   │    │
│  │  │  • Secrets: DB connection, JWT secret, Redis, Storage        │   │    │
│  │  └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
          ACCEPT_EULA: Y
          SA_PASSWORD: YourStrong@Passw0rd
        ports:
          - 1433:1433
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Run tests
        run: npm test
        env:
          NODE_ENV: test
          DB_HOST: localhost
          DB_USER: sa
          DB_PASSWORD: YourStrong@Passw0rd
          REDIS_HOST: localhost
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run database migrations
        run: npm run db:migrate
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
      
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v3
        with:
          app-name: 'notekeeper-bhogarai'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
      
      - name: Azure logout
        run: az logout
```

## Docker Configuration

### Production Dockerfile
```dockerfile
FROM node:20-alpine

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
RUN chown -R nodejs:nodejs /usr/src/app
USER nodejs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

CMD ["node", "src/server.js"]
```

### Development Docker Compose
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DB_HOST=sqlserver
      - REDIS_HOST=redis
    volumes:
      - .:/usr/src/app
      - /usr/src/app/node_modules
    depends_on:
      - sqlserver
      - redis

  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong@Passw0rd
      - MSSQL_PID=Express
    ports:
      - "1433:1433"
    volumes:
      - sql_data:/var/opt/mssql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  sql_data:
  redis_data:
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY STACK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Application Performance Monitoring (APM)                            │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Azure Application Insights                                        │    │
│  │    - Request tracking                                                │    │
│  │    - Dependency tracking (SQL, Redis, HTTP)                          │    │
│  │    - Exception logging                                               │    │
│  │    - Custom events and metrics                                       │    │
│  │    - Performance counters                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Logging                                                             │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Winston (Application Logs) - JSON format, structured logging      │    │
│  │  • Morgan (HTTP Access Logs) - Combined format in production         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Health Checks                                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Endpoint: GET /health                                               │    │
│  │  Checks: Database connectivity, Redis connectivity, Disk space       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Alerting Rules                                                      │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • High Error Rate: > 5% in 5 minutes                                │    │
│  │  • High Response Time: p95 > 1000ms                                  │    │
│  │  • Low Availability: < 99% in 5 minutes                              │    │
│  │  • Memory Usage: > 85%                                               │    │
│  │  • CPU Usage: > 80% for 5 minutes                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Disaster Recovery

| Component | Backup Type | Frequency | Retention |
|-----------|-------------|-----------|-----------|
| Azure SQL | Automated | Daily | 35 days |
| Azure SQL | Long-term | Weekly | 52 weeks |
| Blob Storage | Geo-redundant | Continuous | 30 days |
| Redis | RDB snapshots | Hourly | 24 hours |

**Recovery Objectives:**
- **RPO (Recovery Point Objective)**: 1 hour
- **RTO (Recovery Time Objective)**: 4 hours
