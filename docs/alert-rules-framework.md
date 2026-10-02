# observability-blueprint: Alert Rules Framework

## Alert Philosophy

**Core Principle:** Alert = actionable signal, not noise.

**Bad alert:** Fires 100 times/day, engineer ignores it
**Good alert:** Fires 5 times/month, engineer knows exactly what to do

---

## Alert Severity Levels

### 🔴 CRITICAL (Page on-call immediately)

**Characteristics:**
- User-facing impact (payments failing, settlement delayed)
- Requires immediate action (<5 minutes to respond)
- Fires rarely (< 1/week if well-tuned)
- Warrants escalation

**Examples:**
```yaml
- HighSettlementLatency (P99 > 5s)
- PaymentGatewayDown (availability < 99.95%)
- ComplianceControlFailed (control violation)
- DatabaseConnectionPoolExhausted (no connections left)
- OutOfMemory (memory > 95%)
```

**Routing:** PagerDuty (instant page)
**Response Time SLA:** 5 minutes
**False Positive Rate:** <5%

---

### 🟡 WARNING (Alert via Slack, no page)

**Characteristics:**
- Degradation detected, not critical failure
- Action needed within 30 minutes
- May need escalation if not resolved
- Fires multiple times/day (acceptable)

**Examples:**
```yaml
- HighDatabaseQueryLatency (P95 > 100ms)
- CostAnomaly (15% increase week-over-week)
- HighCPUUsage (80-90% utilization)
- HighErrorRate (0.05% - between normal 0.01% and critical 0.1%)
- PersistentVolumeLow (disk > 80% full)
```

**Routing:** Slack #alerts channel (visible, not intrusive)
**Response Time SLA:** 30 minutes
**False Positive Rate:** <20% acceptable

---

### ⚪ INFO (Email digest, no Slack)

**Characteristics:**
- Informational, not actionable in real-time
- Trend data or reporting
- Can wait until next morning
- Fires frequently (ok)

**Examples:**
```yaml
- DailyAlertHealthCheck (summary of all alerts)
- CostSummary (daily infrastructure spend)
- ComplianceAuditReady (monthly audit evidence available)
- MetricIngestationRate (metrics collected today)
```

**Routing:** Email digest (morning, batched)
**Response Time SLA:** Next business day
**False Positive Rate:** N/A

---

## Alert Rule Structure

Every alert must have:

```yaml
- alert: <NAME>                    # CamelCase, self-documenting
  expr: <PROMQL>                  # Query that triggers alert
  for: <DURATION>                 # How long before firing (noise filter)
  labels:                         # Metadata
    severity: <critical|warning|info>
    team: <platform|finance|compliance>
    sli: <which_SLI_this_covers>
  annotations:                    # Human-readable details
    summary: "..."                # One-liner (shown in Slack)
    description: "..."            # Detailed context
    runbook: "..."                # Link to runbook
    dashboard: "..."              # Link to relevant dashboard
```

---

## 10 Template Alert Rules (Ready to Use)

### 1. Settlement Latency (CRITICAL)
```yaml
- alert: HighSettlementLatency
  expr: |
    histogram_quantile(0.99,
      rate(settlement_latency_seconds_bucket[5m])
    ) > 5
  for: 1m
  labels:
    severity: critical
    team: platform
    sli: settlement_latency
  annotations:
    summary: "Settlement latency {{ $value | humanizeDuration }} (SLO: <5s)"
    description: "P99 settlement latency is above threshold. Check settlement-api logs for errors."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-HighSettlementLatency"
    dashboard: "http://grafana:3000/d/settlement-health"
```

### 2. Transaction Success Rate (CRITICAL)
```yaml
- alert: HighTransactionErrorRate
  expr: |
    (sum(rate(transactions_failed_total[5m])) /
     sum(rate(transactions_total[5m]))) > 0.001
  for: 2m
  labels:
    severity: critical
    team: platform
    sli: transaction_success_rate
  annotations:
    summary: "Transaction error rate {{ $value | humanizePercentage }} (SLO: <0.1%)"
    description: "More than 0.1% of transactions failing. Check payment-api and gateway."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-HighTransactionErrorRate"
    dashboard: "http://grafana:3000/d/payment-api"
```

### 3. Payment Gateway Unavailable (CRITICAL)
```yaml
- alert: PaymentGatewayUnavailable
  expr: |
    (sum(rate(gateway_calls_success[5m])) by (gateway) /
     sum(rate(gateway_calls_total[5m])) by (gateway)) < 0.9995
  for: 1m
  labels:
    severity: critical
    team: platform
    sli: gateway_availability
  annotations:
    summary: "{{ $labels.gateway }} unavailable ({{ $value | humanizePercentage }})"
    description: "Payment gateway {{ $labels.gateway }} is not responding."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-GatewayUnavailable"
    dashboard: "http://grafana:3000/d/payment-gateways"
```

### 4. Database Connection Pool Exhausted (CRITICAL)
```yaml
- alert: DatabaseConnectionPoolExhausted
  expr: |
    (database_connection_pool_active / database_connection_pool_max) > 0.95
  for: 2m
  labels:
    severity: critical
    team: platform
    sli: database_availability
  annotations:
    summary: "DB pool {{ $labels.pool }} is {{ $value | humanizePercentage }} full"
    description: "Connection pool running out. Scale up or reduce connections."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-ConnectionPoolExhausted"
    dashboard: "http://grafana:3000/d/database-health"
```

### 5. Memory Critical (CRITICAL)
```yaml
- alert: OutOfMemory
  expr: |
    (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.95
  for: 2m
  labels:
    severity: critical
    team: platform
    sli: infrastructure_resources
  annotations:
    summary: "{{ $labels.instance }} memory {{ $value | humanizePercentage }} (critical)"
    description: "Node running out of memory. Kill non-essential processes or add RAM."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-OutOfMemory"
    dashboard: "http://grafana:3000/d/infrastructure"
```

### 6. Compliance Control Violation (CRITICAL)
```yaml
- alert: ComplianceDrift
  expr: compliance_control_violations_total > 0
  for: 1m
  labels:
    severity: critical
    team: compliance
    sli: compliance_controls
  annotations:
    summary: "Compliance control {{ $labels.control_id }} failed"
    description: "FCA/SOX control violation detected. Immediate action required."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-ComplianceDrift"
    dashboard: "http://grafana:3000/d/compliance-drift"
```

### 7. Database Slow Queries (WARNING)
```yaml
- alert: HighDatabaseLatency
  expr: |
    histogram_quantile(0.95,
      rate(database_query_duration_seconds_bucket[5m])
    ) > 0.1
  for: 5m
  labels:
    severity: warning
    team: platform
    sli: database_latency
  annotations:
    summary: "DB query latency {{ $value | humanizeDuration }} (SLO: <100ms)"
    description: "Database queries are slow. Check for missing indices or lock contention."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-SlowQueries"
    dashboard: "http://grafana:3000/d/database-performance"
```

### 8. Cost Anomaly (WARNING)
```yaml
- alert: CostAnomaly
  expr: |
    (cost_per_transaction - avg_over_time(cost_per_transaction[7d])) >
    avg_over_time(cost_per_transaction[7d]) * 0.15
  for: 5m
  labels:
    severity: warning
    team: finance
    sli: cost_efficiency
  annotations:
    summary: "Cost increased {{ $value | humanizePercentage }} above average"
    description: "Infrastructure cost spike detected. Review daily spend breakdown."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-CostAnomaly"
    dashboard: "http://grafana:3000/d/cost-intelligence"
```

### 9. High CPU Usage (WARNING)
```yaml
- alert: HighCPUUsage
  expr: |
    (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) > 0.8
  for: 5m
  labels:
    severity: warning
    team: platform
    sli: infrastructure_resources
  annotations:
    summary: "{{ $labels.instance }} CPU {{ $value | humanizePercentage }}"
    description: "CPU approaching limit. Investigate top processes or scale horizontally."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-HighCPU"
    dashboard: "http://grafana:3000/d/infrastructure"
```

### 10. PersistentVolume Low (WARNING)
```yaml
- alert: PersistentVolumeLow
  expr: |
    (kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes) > 0.8
  for: 5m
  labels:
    severity: warning
    team: platform
    sli: infrastructure_resources
  annotations:
    summary: "{{ $labels.persistentvolumeclaim }} {{ $value | humanizePercentage }} full"
    description: "Disk running low. Increase PVC size or clean up old data."
    runbook: "https://github.com/yourorg/observability-blueprint/wiki/Runbook-PVLow"
    dashboard: "http://grafana:3000/d/infrastructure"
```

---

## Alert Routing Rules (Alertmanager)

```yaml
# alertmanager.yml
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  
  routes:
    # Critical → PagerDuty (instant page)
    - match:
        severity: critical
      receiver: 'pagerduty'
      group_wait: 0s        # Page immediately
      repeat_interval: 5m   # Re-page every 5 min if not acked
    
    # Warning → Slack
    - match:
        severity: warning
      receiver: 'slack'
      group_wait: 30s       # Batch for 30s to avoid spam
      repeat_interval: 4h   # Re-notify every 4 hours
    
    # Info → Email digest
    - match:
        severity: info
      receiver: 'email'
      group_wait: 1h        # Batch hourly
      repeat_interval: 24h  # Once per day

# Receivers
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '{{ env "PAGERDUTY_KEY" }}'
        description: '{{ .GroupLabels.alertname }}'
  
  - name: 'slack'
    slack_configs:
      - api_url: '{{ env "SLACK_WEBHOOK_URL" }}'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
  
  - name: 'email'
    email_configs:
      - to: 'alerts@company.com'
        from: 'prometheus@company.com'
```

---

## Alert Testing Strategy

```bash
# Test alert in Prometheus (before deploying)
# 1. Load alert rules into Prometheus
# 2. Go to http://prometheus:9090/alerts
# 3. Look for "PENDING" or "FIRING" state
# 4. If PENDING for duration=1m, it fires in 1 minute

# 2. Chaos test (inject metric, verify alert fires)
python3 chaos_test.py --scenario high_latency --duration 2m

# 3. Silence alert during maintenance
# In Prometheus/Alertmanager UI:
# Silences → New Silence → select alert, set duration
```

---

## Alert SLO

**You should be able to answer:**
1. Detection time: <30 seconds (from issue to alert fired)
2. Notification time: <5 seconds (from alert to Slack/PagerDuty)
3. False positive rate: <5% for critical alerts
4. Response time: <5 minutes for critical alerts

**If not met, tune the alert rules.**
