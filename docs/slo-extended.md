# observability-blueprint: Extended SLI/SLO Framework (10 Total Metrics)

## Recap: 5 Core SLIs (From Day 1)
1. Settlement Processing Latency (P99 < 5s)
2. Transaction Success Rate (>99.9%)
3. Cost Per Transaction (<$0.01)
4. Compliance Control Status (100%)
5. Incident Detection Time (<30s)

---

## NEW: 5 Extended SLIs (Day 2 Addition)

### SLI #6: Payment Gateway Availability
**What:** Percentage of time payment processors are reachable

**Measurement:**
gateway_availability = successful_gateway_calls / total_gateway_calls

**Threshold (SLO):** >99.95% (allows 21 minutes downtime/month)

rate(gateway_calls_success[5m]) / rate(gateway_calls_total[5m]) > 0.9995

**Why this number?**
- Payment processors are external (Stripe, Wise, ACH Network)
- You don't control their uptime, but you need to detect when they're down
- 99.95% = industry standard for fintech integrations
- If Stripe is down, you should know in <1 minute, not 4 hours

**Alert Rule:**
```yaml
- alert: PaymentGatewayUnavailable
  expr: |
    (rate(gateway_calls_success[5m]) / rate(gateway_calls_total[5m])) < 0.9995
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "{{ $labels.gateway }} availability {{ $value | humanizePercentage }}"
```

**Fintech Context:**
- Your customer can't complete payment if Stripe is down
- This alert pages the on-call engineer immediately
- Runbook: "Check Stripe status page, fallback to Wise"

---

### SLI #7: Database Query Performance (P95)
**What:** How long does the median fast query take?

**Measurement:**
P95(query_duration_ms)

**Threshold (SLO):** <100ms for 95% of queries

histogram_quantile(0.95, rate(db_query_duration_ms_bucket[5m])) < 100

**Why this number?**
- Settlement queries: typically 10-50ms
- Report queries: 50-200ms
- P95 at 100ms = queries are slow
- If P95 > 100ms, something is wrong (missing index, lock contention, etc.)

**Alert Rule:**
```yaml
- alert: SlowDatabaseQueries
  expr: |
    histogram_quantile(0.95, rate(db_query_duration_ms_bucket[5m])) > 100
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Database P95 latency {{ $value | humanizeDuration }}"
```

**Fintech Context:**
- Slow queries = settlement delays
- This is a **warning** not critical (immediate action not required)
- Alert goes to Slack (not paged)
- Runbook: "Check slow query log, add index, restart pool"

---

### SLI #8: API Error Rate (by endpoint)
**What:** What percentage of API calls are returning errors?

**Measurement:**
error_rate = error_responses / total_responses

**Threshold (SLO):** <0.1% (10 errors per 10,000 calls)
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) < 0.001

**Why this number?**
- 0.1% error rate = 1 failed payment per 1,000 attempts
- For $2B GMV = ~6,850 failures/year
- This is normal wear-and-tear (retries handle it)
- >0.1% = something is broken

**Alert Rule:**
```yaml
- alert: HighAPIErrorRate
  expr: |
    (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 0.001
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "API error rate {{ $value | humanizePercentage }} (threshold: 0.1%)"
```

**Fintech Context:**
- Errors = customers can't move money
- This pages on-call immediately
- Most common cause: connection pool exhaustion
- Runbook: "Check connection pool size, scale up, restart"

---

### SLI #9: Infrastructure Resource Utilization
**What:** Are we running out of CPU/memory/disk?

**Measurement (CPU):**
cpu_utilization = cpu_used / cpu_available

**Threshold (SLO):** <80% during peak hours
(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) < 0.8

**Why this number?**
- <70% = wasting money on oversized instances
- 70-80% = good (headroom for spikes)
- 80-90% = approaching limit (risk of throttling)
- >90% = emergency (auto-scale or page on-call)

**Alert Rules:**
```yaml
- alert: HighCPUUsage
  expr: (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "CPU usage {{ $value | humanizePercentage }}"

- alert: CriticalMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Memory usage {{ $value | humanizePercentage }}"
```

**Fintech Context:**
- High CPU = slower queries = slower settlements
- This is a **warning** (action needed but not emergency)
- Runbook: "Check which process is consuming, scale if needed"

---

### SLI #10: Data Retention & Compliance Lag
**What:** Are we keeping audit logs as required by FCA?

**Measurement:**
compliance_retention = logs_in_immutable_storage_days

**Threshold (SLO):** ≥ 7 years (2,555 days) for transaction logs
days_in_s3_glacier ≥ 2555

**Why this number?**
- FCA requires 7-year audit trail
- PCI-DSS requires 1 year on-site, 3 years archived
- SOX requires 7 years
- If this fails = audit finding

**Alert Rule:**
```yaml
- alert: ComplianceRetentionMissing
  expr: days_in_s3_glacier < 2555
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Logs only retained {{ $value }} days (SLO: 2555 days/7 years)"
```

**Fintech Context:**
- This is 100% compliance, not optional
- If alert fires = audit is at risk
- Runbook: "Check S3 lifecycle policies, enable Glacier archive"

---

## Summary: 10 SLIs Across 5 Dimensions

| Dimension | SLI | SLO | Owner | Alert Priority |
|-----------|-----|-----|-------|-----------------|
| **Latency** | Settlement P99 | <5s | Trading Ops | 🔴 Critical |
| | DB Query P95 | <100ms | Platform Eng | 🟡 Warning |
| **Availability** | Transaction Success | >99.9% | Platform Eng | 🔴 Critical |
| | Gateway Availability | >99.95% | Platform Eng | 🔴 Critical |
| | API Error Rate | <0.1% | Platform Eng | 🔴 Critical |
| **Cost** | Cost Per Transaction | <$0.01 | Finance | 🟡 Warning |
| **Resources** | CPU Usage | <80% | Platform Eng | 🟡 Warning |
| | Memory Usage | <90% | Platform Eng | 🔴 Critical |
| **Compliance** | Control Status | 100% | Compliance | 🔴 Critical |
| | Retention Days | ≥2555 | Compliance | 🔴 Critical |

---

## Error Budgets (Updated)

**Monthly error budget for critical SLIs:**

| SLI | SLO | Monthly Budget | Usage | Status |
|-----|-----|----------------|-------|--------|
| Settlement Latency | 99% uptime | 7.2 min | — | ✅ |
| Transaction Success | 99.9% | 4.3 min errors | — | ✅ |
| Gateway Availability | 99.95% | 21.6 min | — | ✅ |
| API Error Rate | 99.9% error-free | 4.3 min | — | ✅ |
| Memory Usage | 90% threshold | 0 breaches | — | ✅ |
| Compliance Controls | 100% | 0 failures | — | ✅ |

---

## Interview Use Case

**Hiring Manager:** "You mention 10 SLIs. How did you decide which 10?"

**Your Answer:**
> "I mapped SLIs across 5 dimensions: latency (settlement + database), availability (transactions + gateway + API), cost (cost per transaction), resources (CPU + memory), and compliance (controls + retention).
>
> Each SLI traces back to a business outcome:
> - Settlement latency < 5s → customers get funds fast
> - Gateway availability > 99.95% → payment processor is responsive
> - API error rate < 0.1% → payment flow is stable
> - Memory < 90% → no throttling during peak
> - Compliance retention ≥ 7 years → audit ready
>
> The thresholds are all justified by either industry standards (FCA 7-year rule) or empirical measurement (normal settlement latency is 200ms, so P99 at 5s is a real anomaly).
>
> This gives us 10 metrics to watch, each actionable, each tied to a business outcome."

