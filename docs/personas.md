# observability-blueprint: User Personas

## Persona 1: Trading Ops Engineer 🚀

**Who:** On-call engineer responsible for settlement uptime
**Role:** Typical fintech: VP of Platform Engineering, Platform Engineer, SRE
**Problem:** Settlement delays = customers can't access funds = angry support tickets

### What They Need
- **Primary metric:** P99 settlement latency (threshold: 5 seconds)
- **Alert:** Fires in <30 seconds when latency spikes
- **Dashboard:** Real-time visibility (settlement health, by region, by processor)
- **Runbook:** "Settlement is slow-what do I check?" (5-minute diagnosis)

### Sample Dashboard: "Settlement Health"
Panels:
1. P99 Latency by Processor (card vs ACH vs wire)
2. Success Rate (7-day rolling)
3. Regional Breakdown (US, EU, APAC)
4. Cost per Transaction (real-time)
5. Alert History (last 7 days)

### Alert Rules for Trading Ops
- `HighSettlementLatency`: P99 > 5s → Page immediately
- `SettlementQueueBacklog`: >10k pending → Page with urgency
- `PaymentGatewayFailure`: Stripe/Wise API errors > 0.1% → Page

### Success Criteria
- Incident detection: <30 seconds
- Incident resolution: <15 minutes (with runbook)
- False positive rate: <1% (no alert fatigue)

---

## Persona 2: Finance Controller 💰

**Who:** Chief Financial Officer or Financial Planning & Analysis (FP&A) manager
**Problem:** "Where is our money going? Why are infrastructure costs spiraling?"

### What They Need
- **Primary metric:** Cost per transaction (hourly granularity)
- **Visibility:** Breakdown by service (API gateway, database, storage)
- **Anomaly detection:** "Cost increased 15% week-over-week. Why?"
- **Forecast:** 30-day cost projection

### Sample Dashboard: "Cost Intelligence"
Panels:
1. Daily Cost Trend (last 30 days)
2. Cost Breakdown by Service (pie chart)
3. Cost per Transaction (real-time vs average)
4. Waste Detection (unused resources)
5. Cost Forecast (next 30 days)
6. RI Utilization (reserved instances)

### Alert Rules for Finance
- `CostAnomalyDetected`: Cost spike >15% week-over-week → Slack alert
- `HighDatabaseCost`: DB cost >$X/day → Email with recommendations
- `StorageWaste`: Unused disks >100GB → Slack alert

### Sample Insight (from data)
- Database indices: 12 unused, costing $400/month
- Log verbosity: DEBUG level, costing $1,900/month (vs INFO)
- Compute: Oversized t3.2xlarge → could rightsize to t3.xlarge, save $700/month

### Success Criteria
- Monthly cost review: <2 hours (vs 2 days manual analysis)
- Savings identified: >$50k/year
- CFO confidence: "I see where every dollar goes"

---

## Persona 3: Compliance Officer ⚖️

**Who:** Chief Compliance Officer, Compliance Manager, Internal Audit
**Problem:** "FCA audit is in 60 days. Can you prove we meet controls?"

### What They Need
- **Audit trail:** Transaction settlement history (immutable, 7-year retention)
- **Change management:** Who changed alert rules and when?
- **Compliance proof:** "Here's evidence we meet SYSC 13 governance"
- **Control status:** Are encryption, RBAC, MFA all active?

### Sample Dashboard: "Compliance Drift"
Panels:
1. Unencrypted Data Detection (real-time)
2. Secret Rotation Timeline (last 90 days)
3. Audit Log Ingestion Rate (>1M/day required)
4. Configuration Change History (git log)
5. FCA Control Status (pass/fail checklist)

### Alert Rules for Compliance
- `UnencryptedDataDetected`: Secret or PII in logs → Page compliance officer immediately
- `SecretExposedInLogs`: Datadog API key found → Page + rotate secret
- `ComplianceDriftDetected`: Control failed (e.g., encryption off) → Page

### Compliance Evidence (Auto-Generated)
- Audit trail: `compliance/audit-trail-2024-01.csv`
- Transaction ledger: `compliance/settlement-ledger.csv` (2.3 transactions)
- Configuration changes: `compliance/config-changes.json`
- Access log: `compliance/access-audit.json`

### FCA Questions & Answers
| Question | Answer | Evidence |
|----------|--------|----------|
| "Show transaction audit trail" | [Link to Grafana query] | 2.3M rows in <5 seconds |
| "Prove change control" | [GitHub PR #123, approved] | git log, PR approvals |
| "Prove encryption" | [KMS key ID + rotation] | aws kms describe-key |

### Success Criteria
- Audit readiness: 100% ("No findings")
- Response time to audit questions: <5 minutes (vs 2+ days manual)
- Compliance confidence: "We're ready for any regulatory inspection"

---

## Dashboard Access by Persona
| Dashboard | Trading Ops | Finance | Compliance |
|-----------|------------|---------|-----------|
| Settlement Health | ✅ Owner | 🟡 View | — |
| Cost Intelligence | 🟡 View | ✅ Owner | 🟡 View |
| Compliance Drift | — | — | ✅ Owner |
| Operations | ✅ Owner | — | 🟡 View |

---

## Alert Routing by Persona
| Severity | Trading Ops | Finance | Compliance |
|----------|------------|---------|-----------|
| Critical | 🔴 Page (PagerDuty) | — | 🔴 Page (if compliance) |
| Warning | 🟡 Slack #alerts | 🟡 Slack #finance | 🟡 Slack #compliance |
| Info | — | 📧 Email digest | — |

---

## Interview Use Case
**Hiring Manager:** "Walk me through how your observability system serves different users."

**Your Answer:**
> "I designed 3 personas: Trading Ops needs sub-minute alert latency (settlement SLA), Finance needs cost visibility per transaction (CFO cares about margins), and Compliance needs audit proof (FCA audit readiness).
>
> Each persona has a dashboard:
> 1. Settlement Health → P99 latency, success rate, regional breakdown
> 2. Cost Intelligence → Cost per transaction, waste detection, forecasts
> 3. Compliance Drift → Unencrypted data detection, audit trail, control status
>
> Alert routing is severity + owner based:
> - Critical settlement issues → Page trading ops immediately
> - Cost anomalies → Slack to finance team
> - Compliance drift → Page compliance officer
>
> This means each team sees only what they care about, but they all trust the data source."
