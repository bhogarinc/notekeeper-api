# NoteKeeper On-Call Runbook Template

## Quick Reference

| Item | Details |
|------|---------|
| **Service** | NoteKeeper API |
| **Primary On-Call** | {{PRIMARY_ONCALL}} |
| **Secondary On-Call** | {{SECONDARY_ONCALL}} |
| **Escalation Manager** | {{ESCALATION_MANAGER}} |
| **Slack Channel** | #sre-oncall |
| **PagerDuty Service** | NoteKeeper-Production |

---

## Severity Levels

### SEV-1: Critical - Service Down
- **Criteria**: Complete service unavailability, data loss, security breach
- **Response Time**: 5 minutes
- **Communication**: Immediate Slack + PagerDuty + Manager notification
- **Actions**:
  1. Acknowledge alert within 5 minutes
  2. Assess impact scope
  3. Initiate incident bridge call if needed
  4. Page secondary on-call if unresolved in 15 minutes

### SEV-2: High - Degraded Service
- **Criteria**: Major functionality impaired, >5% error rate, >2s latency p99
- **Response Time**: 15 minutes
- **Communication**: Slack notification + PagerDuty
- **Actions**:
  1. Acknowledge alert within 15 minutes
  2. Check dashboards for root cause
  3. Apply mitigation if available
  4. Escalate if unresolved in 30 minutes

### SEV-3: Medium - Minor Issue
- **Criteria**: Non-critical functionality affected, elevated error rates
- **Response Time**: 1 hour
- **Communication**: Slack notification
- **Actions**:
  1. Acknowledge alert
  2. Create ticket for investigation
  3. Monitor for escalation

### SEV-4: Low - Observation
- **Criteria**: Informational, no immediate impact
- **Response Time**: Next business day
- **Communication**: Ticket creation

---

## Common Alert Responses

### Alert: `NoteKeeperAPIDown`

**Initial Checks:**
```bash
# Check health endpoint
curl -f https://notekeeper-bhogarai.azurewebsites.net/health

# Check Azure App Service status
az webapp show --name notekeeper-bhogarai --resource-group notekeeper-rg

# View recent logs
az webapp log tail --name notekeeper-bhogarai --resource-group notekeeper-rg
```

**Common Causes:**
1. **Application Crash**: Check container logs for stack traces
2. **Database Connectivity**: Verify PostgreSQL connection string and firewall rules
3. **Memory Exhaustion**: Check App Service plan scaling
4. **Deployment Issue**: Rollback to previous version if recent deployment

**Mitigation Steps:**
1. Restart App Service: `az webapp restart --name notekeeper-bhogarai`
2. Scale up App Service plan if resource-constrained
3. Check database connection pool status
4. Verify environment variables are correctly set

---

### Alert: `NoteKeeperHighErrorRate`

**Initial Checks:**
```bash
# Query Prometheus for error breakdown
curl -G 'http://prometheus:9090/api/v1/query' \
  --data-urlencode 'query=sum(rate(http_requests_total{service="notekeeper-api",status=~"5.."}[5m])) by (endpoint, status)'

# Check recent application logs
kubectl logs -l app=notekeeper-api --tail=100 | grep ERROR
```

**Common Causes:**
1. **Database Connection Issues**: Connection pool exhaustion, query timeouts
2. **External Service Failures**: Third-party API unavailability
3. **Code Deployment Bug**: Recent deployment introduced errors
4. **Traffic Spike**: Unexpected load causing resource exhaustion

**Mitigation Steps:**
1. Identify error endpoint from metrics
2. Check database connection pool utilization
3. Review recent deployments - consider rollback
4. Scale horizontally if load-related
5. Enable circuit breaker if external service failing

---

### Alert: `NoteKeeperHighLatency`

**Initial Checks:**
```bash
# Check p99 latency by endpoint
curl -G 'http://prometheus:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))'

# Check database query performance
# Query pg_stat_statements for slow queries
```

**Common Causes:**
1. **Slow Database Queries**: Missing indexes, table bloat
2. **N+1 Query Problem**: Inefficient ORM usage
3. **External API Latency**: Third-party service slowdown
4. **Resource Contention**: CPU/memory constraints

**Mitigation Steps:**
1. Identify slow endpoints from traces (Jaeger)
2. Review database query plans
3. Check for missing indexes
4. Scale resources if needed
5. Implement caching for frequently accessed data

---

### Alert: `PostgreSQLPrimaryDown`

**Initial Checks:**
```bash
# Check PostgreSQL status
kubectl get pods -l app=postgresql

# Check logs
kubectl logs -l app=postgresql --tail=50

# Check connection from application
psql $DATABASE_URL -c "SELECT 1"
```

**Common Causes:**
1. **Pod Crash**: OOMKilled, resource limits
2. **Storage Issues**: Disk full, PVC problems
3. **Network Connectivity**: Service endpoint issues
4. **Configuration Error**: Invalid postgresql.conf settings

**Mitigation Steps:**
1. Check if failover to replica occurred
2. Restart PostgreSQL pod if stuck
3. Verify disk space and expand if needed
4. Check for replication lag on standby
5. Contact DBA team for complex issues

---

## Escalation Procedures

### Escalation Path

1. **Primary On-Call** (First 30 minutes)
   - Acknowledge and investigate
   - Attempt mitigation
   - Communicate in #sre-oncall

2. **Secondary On-Call** (After 30 minutes)
   - Join incident response
   - Provide additional expertise
   - Assist with communication

3. **SRE Team Lead** (After 1 hour)
   - Strategic decision making
   - Stakeholder communication
   - Resource allocation

4. **Engineering Manager** (SEV-1 or >2 hours)
   - Executive communication
   - Business impact assessment
   - Post-incident review scheduling

### Communication Templates

**Incident Started:**
```
🚨 INCIDENT ALERT - SEV-{1/2/3}
Service: NoteKeeper API
Alert: {ALERT_NAME}
Impact: {BRIEF_DESCRIPTION}
Responder: @{PRIMARY_ONCALL}
Status: Investigating
Thread: {SLACK_THREAD_LINK}
```

**Status Update (Every 30 min for SEV-1/2):**
```
📊 INCIDENT UPDATE - SEV-{1/2}
Duration: {MINUTES} minutes
Current Status: {INVESTIGATING/MITIGATING/MONITORING/RESOLVED}
Impact: {CURRENT_IMPACT}
Next Steps: {ACTION_ITEMS}
ETA: {ESTIMATED_RESOLUTION}
```

**Incident Resolved:**
```
✅ INCIDENT RESOLVED - SEV-{1/2/3}
Duration: {MINUTES} minutes
Resolution: {BRIEF_DESCRIPTION}
Root Cause: {PRELIMINARY_ANALYSIS}
Post-Mortem: Scheduled for {DATE}
```

---

## Post-Incident Actions

1. **Immediate (Within 1 hour)**
   - Write incident summary
   - Create JIRA ticket for follow-up
   - Update status page if customer-facing

2. **Short-term (Within 24 hours)**
   - Conduct preliminary review
   - Document timeline
   - Identify immediate action items

3. **Long-term (Within 1 week)**
   - Schedule post-mortem meeting
   - Create remediation tickets
   - Update runbooks with learnings

---

## Useful Commands

```bash
# View application logs
az webapp log tail --name notekeeper-bhogarai --resource-group notekeeper-rg

# Check Prometheus metrics
curl http://prometheus:9090/api/v1/query?query=up{job="notekeeper-api"}

# Query Elasticsearch logs
curl -X GET "elasticsearch:9200/notekeeper-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"log.level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}'

# View distributed traces
open http://jaeger:16686/search?service=notekeeper-api

# Check Grafana dashboards
open https://grafana.internal/d/notekeeper-api
```

---

## Contacts

| Role | Name | Contact |
|------|------|---------|
| SRE Team Lead | {{SRE_LEAD}} | {{SRE_LEAD_CONTACT}} |
| DBA Team | {{DBA_TEAM}} | {{DBA_CONTACT}} |
| Security Team | {{SECURITY_TEAM}} | {{SECURITY_CONTACT}} |
| Product Owner | {{PRODUCT_OWNER}} | {{PRODUCT_CONTACT}} |
| Azure Support | - | https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade |
