# observability-blueprint: System Architecture

## Overview

Production observability stack for fintech, designed for:
- **150k metrics/sec** (from 50+ microservices)
- **High availability** (3-node replicas)
- **Cost efficiency** (65% cheaper than Datadog)
- **Compliance** (FCA/SOX/GDPR ready)

## Architecture Diagram

```
╔════════════════════════════════════════════════════════════════════════════╗
║                        FINTECH APPLICATIONS LAYER                          ║
║                                                                            ║
║   Payment API  │  Settlement Engine  │  Risk Engine  │  Other Services     ║
╚════════════════════════════════════════════════════════════════════════════╝
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
        │  PROMETHEUS     │  │    LOKI      │  │    TEMPO     │
        │   (Metrics)     │  │    (Logs)    │  │   (Traces)   │
        │                 │  │              │  │              │
        │  • 150k/sec     │  │  • 100GB/mo  │  │  • 24hr hot  │
        │  • 15d hot      │  │  • 30d hot   │  │  • S3 cold   │
        │  • S3 cold      │  │  • Glacier   │  │              │
        │  • HA: 3x       │  │  • HA: 3x    │  │  • HA: 3x    │
        └────────┬────────┘  └──────┬───────┘  └──────┬───────┘
                 │                  │                 │
                 └──────────────────┬─────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌──────────────────────┐      ┌─────────────────────┐
        │      GRAFANA         │      │   ALERTMANAGER      │
        │    (Dashboards)      │      │   (Alert Routing)   │
        │                      │      │                     │
        │  • Settlement Health │      │  • Severity check   │
        │  • Cost Intelligence │      │  • Deduplication    │
        │  • Compliance Drift  │      │  • Grouping         │
        │  • 3 replicas        │      │  • 3 replicas       │
        └──────────────────────┘      └──────────┬──────────┘
                    │                            │
                    │                ┌───────────┼───────────┐
                    │                │           │           │
                    │                ▼           ▼           ▼
                    │         ┌──────────┐  ┌────────┐  ┌────────┐
                    │         │PagerDuty │  │ Slack  │  │ Email  │
                    │         │(Critical)│  │(Warning)  │(Digest)│
                    │         └──────────┘  └────────┘  └────────┘
                    │
                    └──► [On-call Engineers see dashboards]
```

## Components

### 1. Prometheus (Time-Series Database)
- **Role:** Scrapes metrics from targets (API, K8s, databases)
- **Data Flow:** Pull-based (Prometheus pulls from / metrics endpoint)
- **Storage:** 15-day hot retention on SSD, archive to S3
- **Capacity:** 150k metrics/sec on single instance
- **Trade-off:** Stateful (not cloud-native ideal), but acceptable for observability

**Why Prometheus?**
- Industry standard (Kubernetes, Google, Stripe use it)
- No agent installation needed (targets just expose / metrics)
- Cost-efficient (vs Datadog $2.5k/month)
- Full operational control

### 2. Loki (Log Aggregation)
- **Role:** Collects structured logs from all services
- **Data Flow:** Push-based (fluent-bit → Loki)
- **Storage:** S3 (cheap, compliant with FCA immutability)
- **Retention:** 30 days hot, auto-archive to Glacier
- **Query Language:** LogQL (similar to PromQL)
- **Cardinality:** Labels-only indexing (no full-text search)

**Why Loki?**
- 65% cheaper than CloudWatch
- Immutable backend (compliance requirement)
- LogQL integrates with Grafana
- No high-cardinality problems (because we don't index on customer_id)

### 3. Tempo (Distributed Tracing)
- **Role:** Traces payment flows end-to-end
- **Data Flow:** OTEL (OpenTelemetry) → Tempo
- **Storage:** S3 (archive after 24 hours)
- **Use Case:** "Payment took 5 seconds-trace all microservices involved"
- **Integration:** Grafana datasource

**Why Tempo?**
- Correlates logs + metrics + traces
- Cheap storage (not sampled-we keep everything for 24h)
- Helps debug payment failures

### 4. Grafana (Dashboards & Visualization)
- **Role:** Query Prometheus/Loki/Tempo, display dashboards
- **Storage:** PostgreSQL (RDS for prod)
- **Authentication:** OIDC/SSC
- **HA:** 3 replicas
- **Dashboards:** Version-controlled as JSON

**Why Grafana?**
- Industry standard (everyone knows it)
- Multi-datasource support
- Customizable alerts (although Prometheus is primary)
- Free/open-source

### 5. Alertmanager (Alert Routing)
- **Role:** Routes alerts to Slack, PagerDuty, email
- **Rules:** Severity-based routing (critical → page, warning → Slack)
- **Grouping:** Prevents alert spam
- **HA:** 3 replicas

## Data Flow Example: Settlement Latency Alert
1. Payment API exposes metric: settlement_processing_duration_seconds{processor="settlement-engine"}=6.2
2. Prometheus scrapes every 15 seconds: GET http://payment-api:8080/metrics
3. Prometheus evaluates alert rule: IF p99(settlement_latency) > 5s for 1 minute THEN fire HighSettlementLatency
4. Alertmanager receives alert: { alertname: "HighSettlementlatency", severity: "critical", instance: "payment-api:8080" }
5. Routes to PagerDuty: POST https://events.pagerduty.com/v2/enqueue { "routing_key": "....", "dedup_key": "HighSettlementLatency|payment-api", "payload": { "summary": "Settlment latency 6.2s (threshold: 5s)", "severity": "critical, "source": "observability-blueprint" } }
6. PagerDuty pages on-call engineer (30 seconds after latency spike)

## Scalability Limits

### Prometheus
- **Single instance:** Up to 1M metrics/sec
- **Our volume:** 150k metrics/sec → single instance fine
- **When to shard:** >500k metrics/sec
- **Solution:** Thanos (multi-Prometheus federation)

### Loki
- **Throughput:** No hard limit
- **Storage:** Scales linearly (~$2/GB/month on S3)
- **When to Optimize:** >1TB/day logs

### Grafana
- **Dashboard:** Unlimited
- **Datasources:** 3-5 recommended (Prometheus, Loki, Tempo, etc.)
- **Users:** Scales to thousands with SSO

## Trade-offs

| Decision | Benefit | Trade-off |
|----------|---------|-----------|
| Prometheus pull-based | No agent dependencies | Stateful, not cloud-native |
| Loki labels-only indexing | Cheap storage | Can't search by customer_id in logs |
| Tempo 24h retention | Cheap | Can't trace incidents >24h old |
| Single Prometheus | Simple, cheap | Single point of failure (mitigated with PVC snapshots) |
| Grafana SSO | Security | Requires identity provider setup |

## Disaster Recovery

- **Prometheus PVC:** Daily snapshots to S3
- **Loki data:** Already on S3 (immutable)
- **RTO (Recovery Time):** <2 hours (restore PVC from snapshot)
- **RPO (Recovery Point):** <24 hours (daily snapshots)

## Next Steps

1. Define SLOs (Week 1, Day 1-2)
2. Design alert rules (Week 1, Day 3-4)
3. Implement in Terraform (Week 2)
4. Deploy to staging (Week 4-5)
