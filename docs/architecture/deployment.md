# NoteKeeper Deployment Architecture

## Overview
NoteKeeper is deployed on Microsoft Azure using Infrastructure as Code principles.

## Environment Strategy

### Environments
| Environment | URL | Branch | Purpose |
|------------|-----|--------|---------|
| Development | `localhost:3000` | `feature/*` | Local development |
| Staging | `notekeeper-staging.azurewebsites.net` | `develop` | Integration testing |
| Production | `notekeeper-bhogarai.azurewebsites.net` | `main` | Live application |

## Azure Resource Architecture

### Resource Group
```
rg-notekeeper (Central US)
│
├── App Service Plan: asp-notekeeper
│   ├── SKU: B1 (Basic)
│   ├── Tier: Linux
│   └── Instances: 1 (scalable to 3)
│
├── App Service: notekeeper-bhogarai
│   ├── Runtime: Node.js 20 LTS
│   ├── Deployment: GitHub Actions
│   ├── Slots:
│   │   ├── staging (warm swap)
│   │   └── production
│   └── Configuration:
│       ├── Always On: Enabled
│       ├── HTTPS Only: Enabled
│       ├── Min TLS: 1.2
│       └── Health Check: /health
│
├── Database: notekeeper-db
│   ├── Type: PostgreSQL Flexible Server
│   ├── Version: 15
│   ├── Tier: Burstable B1ms
│   ├── Storage: 32GB
│   ├── Backup: 7-day retention
│   ├── HA: Zone redundant (prod only)
│   └── Firewall: Azure services only
│
├── Cache: notekeeper-cache
│   ├── Type: Azure Cache for Redis
│   ├── Tier: Basic C0
│   ├── Capacity: 250MB
│   └── Eviction: allkeys-lru
│
├── Storage: notekeeperstorage
│   ├── Type: Standard LRS
│   ├── Container: attachments
│   └── CORS: App Service origin only
│
└── Monitoring: appinsights-notekeeper
    ├── Type: Application Insights
    ├── Workspace: log-notekeeper
    └── Retention: 90 days
```

## Network Architecture

### Connectivity
```
Internet
    │
    ▼
┌─────────────────────────────┐
│   Azure Front Door (future) │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│   App Service               │
│   (notekeeper-bhogarai)     │
│                             │
│   ┌─────────────────────┐   │
│   │  Node.js App        │   │
│   │  - Express API      │   │
│   │  - Static SPA       │   │
│   └─────────────────────┘   │
└─────────────────────────────┘
    │
    ├──▶ PostgreSQL (private endpoint)
    │
    ├──▶ Redis (private endpoint)
    │
    └──▶ Blob Storage (private endpoint)
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run test:integration

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: app-build
          path: dist/

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-build
          path: ./dist
      - uses: azure/webapps-deploy@v3
        with:
          app-name: 'notekeeper-staging'
          slot-name: 'production'
          publish-profile: ${{ secrets.AZUREAPPSERVICE_STAGING }}
          package: ./dist

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-build
          path: ./dist
      - uses: azure/webapps-deploy@v3
        with:
          app-name: 'notekeeper-bhogarai'
          slot-name: 'staging'
          publish-profile: ${{ secrets.AZUREAPPSERVICE_PROD }}
          package: ./dist
      - name: Swap slots
        run: |
          az webapp deployment slot swap \
            --resource-group rg-notekeeper \
            --name notekeeper-bhogarai \
            --slot staging \
            --target-slot production
```

### Deployment Process

#### Staging Deployment
1. Push to `develop` branch
2. Run automated tests
3. Build application
4. Deploy to staging slot
5. Run smoke tests
6. Notify team

#### Production Deployment
1. Create PR from `develop` to `main`
2. Code review required
3. Merge to `main`
4. Run full test suite
5. Deploy to production staging slot
6. Health check verification
7. Swap slots (zero downtime)
8. Monitor for 30 minutes
9. Rollback if error rate > 1%

## Configuration Management

### Environment Variables
```bash
# Application
NODE_ENV=production
PORT=8080
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:pass@notekeeper-db.postgres.database.azure.com:5432/notekeeper
DATABASE_SSL=true

# Redis
REDIS_URL=redis://notekeeper-cache.redis.cache.windows.net:6380
REDIS_PASSWORD=***
REDIS_SSL=true

# JWT
JWT_PRIVATE_KEY_PATH=/secrets/jwt-private.pem
JWT_PUBLIC_KEY_PATH=/secrets/jwt-public.pem
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d

# Storage
AZURE_STORAGE_ACCOUNT=notekeeperstorage
AZURE_STORAGE_KEY=***
AZURE_STORAGE_CONTAINER=attachments

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX=100
CORS_ORIGIN=https://notekeeper-bhogarai.azurewebsites.net

# Monitoring
APPINSIGHTS_INSTRUMENTATIONKEY=***
LOG_LEVEL=info
```

### Secret Management
Secrets stored in:
1. **Development**: `.env.local` (gitignored)
2. **Staging**: Azure App Service Configuration
3. **Production**: Azure Key Vault + App Service

## Backup & Disaster Recovery

### Database Backups
- **Automated**: Daily backups, 7-day retention
- **Geo-redundant**: Backups in paired region (Central US → East US 2)
- **Point-in-time**: 7-day recovery window

### Recovery Procedures

#### Database Recovery
```bash
# Restore to point in time
az postgres flexible-server restore \
  --name notekeeper-db-restored \
  --source-server notekeeper-db \
  --restore-time "2026-04-26T00:00:00Z" \
  --resource-group rg-notekeeper
```

#### Application Recovery
1. Rollback to previous deployment:
   ```bash
   az webapp deployment source sync \
     --name notekeeper-bhogarai \
     --resource-group rg-notekeeper
   ```

2. Or swap back to previous slot:
   ```bash
   az webapp deployment slot swap \
     --name notekeeper-bhogarai \
     --resource-group rg-notekeeper \
     --slot production \
     --target-slot staging
   ```

## Scaling Strategy

### Vertical Scaling
| Metric | Current | Scale Up Trigger | Target |
|--------|---------|-----------------|--------|
| CPU | B1 (1 core) | > 70% for 10 min | B2 (2 cores) |
| Memory | 1.75 GB | > 80% for 10 min | B2 (3.5 GB) |
| DB | B1ms | > 80% CPU | B2s |

### Horizontal Scaling
Auto-scaling rules:
- Scale out: CPU > 70% for 5 minutes → +1 instance (max 3)
- Scale in: CPU < 30% for 10 minutes → -1 instance (min 1)

### Database Scaling
- Read replicas for query load (future)
- Connection pooling with PgBouncer (future)

## Monitoring & Alerting

### Metrics Monitored
| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Response Time | > 500ms | > 1000ms | Scale up |
| Error Rate | > 1% | > 5% | Rollback |
| CPU Usage | > 70% | > 85% | Scale out |
| Memory Usage | > 70% | > 85% | Scale up |
| DB Connections | > 80% | > 95% | Alert DBA |

### Alerts
- **Email**: team@company.com
- **Slack**: #alerts-channel
- **PagerDuty**: Critical only (error rate > 5%)

## Security Configuration

### Network Security
- Private endpoints for database and cache
- VNet integration for App Service
- NSG rules restrict traffic

### Application Security
- HTTPS only (TLS 1.2+)
- Security headers via Helmet.js
- WAF enabled (future)

### Data Security
- Encryption at rest: Azure-managed keys
- Encryption in transit: TLS 1.3
- Database TDE enabled

## Cost Estimates

### Monthly Costs (USD)
| Resource | Tier | Monthly Cost |
|----------|------|-------------|
| App Service Plan | B1 | ~$13 |
| PostgreSQL | B1ms | ~$15 |
| Redis Cache | C0 | ~$16 |
| Storage | Standard LRS | ~$5 |
| Application Insights | Pay-as-you-go | ~$10 |
| Bandwidth | 100 GB | ~$9 |
| **Total** | | **~$68/month** |

### Scaling Costs
| Scenario | Monthly Cost |
|----------|-------------|
| Current (1 instance) | ~$68 |
| 3 instances | ~$94 |
| With CDN | ~$110 |
| With Front Door | ~$125 |

---

*Last Updated: April 26, 2026*
