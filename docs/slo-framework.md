# observability-blueprint: SLI/SLO Framework

## What Are SLIs & SLOs?
**SLI (Service Level Indicator):** Actual measured metric (e.g., "P99 latency is 120ms")
**SLO (Service Level Objective):** Target you commit to (e.g., "P99 latency should be <100ms")
**SLA (Service Level Agreement):** Legal consequence if you miss SLO (e.g., "99.95% uptime or customer gets $100 credit")

In fintech: SLOs are critical. You're handling customer money.

---

## Core SLIs for observability-blueprint

### SLI #1: Settlement Processing Latency
**What:** Time from payment initiated → funds settled

**Measurement:**
P99(settlement_processing_duartion_seconds)

**Threshold (SLO):** <5 seconds for 99% of transactions
settlement_processing_duartion_seconds p99 < 5s

**Why this number?**
- Customer expectation: "Funds available in seconds"
- Business: Settlement >10s = customer experience issue
- Reality: Normal is 200-500ms, P99 at 5s is reasonable

**Alert Rule:**
```yaml
- alert: HighSettlmentLatency
  expr: histogram_quantile(0.99, rate(settlement_processing_duration_seconds_bucket[5m])) > 5
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Settlement latency {{ $value }}s (SLO: <5s)"
```

---

### SLI #2: Transaction Success Rate
**What:** Percentage of transactions that complete successfully

**Measurement:**
success_rate = completed_transactions / attempted_transactions

**Threshold (SLO):** >99.9% success (error budget: 0.1%)
rate(transactions_completed[1h]) / rate(transactions_attempted[1h]) > 0.999

**Why this number?**
- 0.1% error = 1 failed transaction per 1,000
- For $2B GMV/year = ~6,850 failures/year
- Acceptable in fintech (not in banking, where SLA is 99.99%)

**Alert Rule:**
```yaml
- alert: HighErrorRate
  expr: |
    (rate(transaction_failures_total[5m]) / rate(transactions_total[5m])) > 0.001
  for: 2m
  severity: critical
```

---

### SLI #3: Cost Per Transaction
**What:** How much infrastructure does each transaction cost?

**Measurement:**
cost_per_transaction = total_monthly_cost / transaction_count

**Threshold (SLO):** <$0.01 per transaction
aws_monthly_cost / sum(transactions) < 0.01

**Why this number?**
- Current: $900/month / 10M transactions/month = $0.00009 per transaction
- SLO: <$0.01 per transaction (100x budget)
- When to optimize: >$0.005 per transaction

**Alert Rule:**
```yaml
- alert: CostAnomaly
  expr: |
    (cost_per_transaction - avg_over_time(cost_over_transaction[7d])) > avg_over_time(cost_per_transaction[7d]) * 0.15
  for: 5m
  severity: warning
```

---

### SLI #4: Compliance Control Status
**What:** Percentage of FCA/SOX controls passing

**Measurement:**
compliance_pass_rate = controls_passing / total_controls

**Threshold (SLO):** 100% (no failed controls)
compliance_control_failures == 0

**Why 100%?**
- Compliance is binary in fintech
- 1 failed control = audit finding
- No budget for "some controls can fail"

**Alert Rule:**
```yaml
- alert: ComplianceDrift
  expr: compliance_control_failures_total > 0
  for: 1m
  severity: critical
```

---

### SLI #5: Incident Detection Time
**What:** How fast do we detect problems?

**Measurement:**
detection_time = alert_fired_time - incident_started_time

**Threshold (SLO):** <30 seconds
AlertManager timestamp - incident timestamp < 30s

**Why 30 seconds?**
- Settlement latency spike should be detected in 1 Prometheus scrape cycle
- Prometheus scrape interval: 15 seconds
- Alert evaluation: 30 seconds (2 cycles)
- Total: ~30 seconds

**Success Criteria:**
```yaml
- If incident starts at T=0
- Prometheus scrapes at T=15 (detects high latency)
- Alert fires at T=30 (meets SLO)
```

---

### Error Budget & Budget Tracking

**Concept:** You have a "budget" of downtime/errors. Once you exceed it, you're in breach.

**Example: Settlement Availability**

Monthly error budget:
SLO: 99.95% uptime Error budget: 1 - 0.9995 = 0.0005 (0.05%) Minutes per month: 30 days x 24 hours x 60 min = 43,200 min Error budget (minutes): 43,200 x 0.0005 = 21.6 minutes

Meaning: **You can afford 21.6 minutes of downtime per month.**

If you have:
- Week 1: 5 min outage (remaining: 16.6 min) ✅
- Week 2: 10 min outage (remaining: 6.6 min) ✅
- Week 3: 8 min outage (remaining: -1.4 min) 🔴 BUDGET EXCEEDED

Once budget exceeded → Freeze deployments, focus on reliability.

**Dashboard Panel: Error Budget**
Current Month: Feb 2024 SLO: 99.95% availability Error Budget: 21.6 minutes Used: 5 minutes Remaining: 16.6 minutes Burn Rate: 0.2 minutes/day (sustainable) Status: ✅ On track

---

## SLO by Team & Alert Priority

| SLI | SLO | Owner | Alert Priority | Budget |
|-----|-----|-------|-----------------|--------|
| Settlement Latency P99 | <5s | Trading Ops | 🔴 Critical | 1 min/month |
| Transaction Success Rate | >99.9% | Platform Eng | 🔴 Critical | 0.1% errors |
| Cost Per Transaction | <$0.01 | Finance | 🟡 Warning | Flexible |
| Compliance Controls | 100% | Compliance | 🔴 Critical | 0 failures |
| Incident Detection | <30s | Platform Eng | 🟡 Info | Target, not SLO |

---

## Next Steps (Week 1, Day 2-3)

1. Define 5 more SLIs (payment gateway latency, database query time, etc.)
2. Create alert rules for each SLI
3. Document threshold justifications
4. Estimate error budgets

---

## Example: How This Drives Business

**Scenario: Settlement latency spike to 8 seconds**

1. T=0: Settlement processor has spike
2. T=15: Prometheus scrapes, detects P99=8s
3. T=30: HighSettlementLatency alert fires
4. T=35: On-call engineer sees Slack + PagerDuty notification
5. T=40: Engineer queries Grafana, identifies root cause (missing database index)
6. T=60: Root cause addressed, latency back to normal
7. T=90: Root cause analysis complete, ticket failed

**Business result:** 60 seconds of latency = $10k in locked transactions (6,850 tx x $1.5 avg).
**Prevented loss:** By detecting in 30 seconds vs 4 hours manual discovery = **$50k+ impact avoided**.

This is your value prop.
