# observability-blueprint: Metrics Taxonomy

## Why Taxonomy Matters

When you have 150k metrics/second, you need a **naming convention** so you can query them.

Example: Instead of random metric names like `latency123` or `perf_x`, use a consistent structure:
service_component_unit{labels}

This way you can query all settlement metrics: `settlement_*` or all latencies: `*_duration_*`

---

## Taxonomy Structure
observability_blueprint_metrics/ ├── settlement/ │ ├── latency │ ├── throughput │ ├── errors │ └── cost ├── payment_api/ │ ├── request_duration │ ├── errors │ ├── active_connections │ └── response_size ├── database/ │ ├── query_duration │ ├── connection_pool │ ├── replication_lag │ └── disk_usage ├── compliance/ │ ├── audit_logs_ingested │ ├── pii_detection_events │ ├── control_violations │ └── retention_days ├── infrastructure/ │ ├── cpu_usage │ ├── memory_usage │ ├── disk_usage │ └── network_io └── business/ ├── gmv_total ├── transaction_count ├── cost_per_transaction └── revenue

---

## Metric Naming Convention

### Rule 1: Type comes first
- `settlement_latency_seconds` (not `latency_in_settlement`)
- `database_query_duration_ms` (not `query_latency_db`)

**Why?** Prometheus sorts metrics alphabetically. Service name first = all settlement metrics cluster together.

### Rule 2: Unit is explicit
- `duration_seconds` (not `duration`)
- `size_bytes` (not `size`)
- `count_total` (not `total_count`)

**Why?** Prevents confusion. 1000 could be milliseconds or microseconds.

### Rule 3: Labels are lowercase
settlement_latency_seconds{processor="stripe", region="us-east-1", p_percentile="99"}

Not:
settlement_latency_seconds{Processor="stripe", Region="us-east-1"}

---

## Complete Metrics List (150k/sec breakdown)

### Settlement Metrics (30% of load = 45k/sec)
```yaml
# Latency
settlement_latency_seconds_bucket{processor, region, le}
settlement_latency_seconds_sum{processor, region}
settlement_latency_seconds_count{processor, region}

# Throughput
settlement_transactions_total{processor, region, status} # counter
settlement_transactions_processing{processor, region} # gauge

# Cost
settlement_cost_usd_total{processor, region} # counter
settlement_cost_per_transaction_usd{processor, region} # gauge

# Errors
settlement_errors_total{processor, region, error_type}
settlement_error_rate{processor, region}
```

### Payment API Metrics (35% of load = 52.5k/sec)
```yaml
# Requests
http_requests_total{method, path, status} # counter
http_request_duration_seconds_bucket{method, path, le}
http_requests_in_progress{method, path} # gauge

# Errors
http_errors_total{method, path, error_type}
http_4xx_errors_total{method}
http_5xx_errors_total{method}

# Connection Pool
api_connections_active{service, pool} # gauge
api_connections_max{service, pool} # gauge
api_connection_wait_seconds{service}
```

### Database Metrics (20% of load = 30k/sec)
```yaml
# Query Performance
database_query_duration_seconds_bucket{query_type, le}
database_slow_queries_total{query_type}

# Connection Pool
database_connection_pool_active{pool_name}
database_connection_pool_idle{pool_name}
database_connection_pool_wait_seconds{pool_name}

# Replication
database_replication_lag_seconds{replica}
database_replication_status{replica} # 0=ok, 1=lagging

# Disk
database_disk_usage_bytes{pool_name}
database_disk_free_bytes{pool_name}
```

### Compliance Metrics (10% of load = 15k/sec)
```yaml
# Audit Logs
audit_logs_ingested_total{source}
audit_logs_processed_total{processor}
audit_log_ingestion_lag_seconds{source}

# Compliance Checks
compliance_control_violations_total{control_id, severity}
compliance_pii_detected_total{pii_type}
compliance_secret_detections_total{secret_type}
compliance_retention_days{log_type} # gauge

# Drift Detection
compliance_drift_events_total{control_id}
compliance_drift_resolved_total{control_id}
```

### Infrastructure Metrics (5% of load = 7.5k/sec)
```yaml
# CPU
node_cpu_usage_percent{node, core}
container_cpu_usage_seconds_total{pod, container}

# Memory
node_memory_usage_percent{node}
container_memory_usage_bytes{pod, container}
container_memory_limit_bytes{pod, container}

# Disk
node_disk_usage_percent{node, mount_point}
node_disk_io_read_bytes_total{node, device}
node_disk_io_write_bytes_total{node, device}

# Network
node_network_bytes_sent_total{node, device}
node_network_bytes_recv_total{node, device}
```

### Business Metrics (Gauge/Low Cardinality)
```yaml
# GMV (Gross Merchandise Volume)
business_gmv_usd_total # counter
business_gmv_current_month_usd # gauge

# Transactions
business_transaction_count_total # counter
business_transaction_success_count_total # counter
business_transaction_error_count_total # counter

# Cost
business_infrastructure_cost_usd_total # counter
business_cost_per_transaction_usd # gauge (updated hourly)

# Revenue
business_revenue_usd_total # counter
business_revenue_per_transaction_usd # gauge
```

---

## Label Cardinality Limits

**Cardinality** = number of unique combinations of label values.

Example: `settlement_latency_seconds{processor, region}`
- If 5 processors and 4 regions = 20 combinations
- If you add `user_id` = 20 × 1,000,000 users = 20 million combinations 🔴

**Rule: Keep cardinality < 1,000 per metric**

```yaml
# ✅ GOOD (20 combinations)
settlement_latency_seconds{processor, region}

# ✅ GOOD (100 combinations = 10 endpoints × 10 error types)
http_errors_total{endpoint, error_type}

# 🔴 BAD (1 million combinations = high user volume)
settlement_latency_seconds{user_id, processor, region}

# 🔴 BAD (unbounded, increases over time)
http_requests_total{url, user_id, timestamp}
```

---

## Scrape Strategy

**How Prometheus collects metrics:**

```yaml
# prometheus.yml scrape config
scrape_configs:
  - job_name: 'settlement-api'
    scrape_interval: 15s
    targets:
      - settlement-api:8080
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod_name
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
```

**Scrape interval = 15 seconds**
- Every 15s, Prometheus pulls `/metrics` from each target
- For 50 targets × 3k metrics each = 150k metrics/sec ✓
- If you increase to 10s scrape = 225k metrics/sec (approaching limit)

---

## Query Examples (Using Taxonomy)

Find all settlement metrics:
```promql
{__name__=~"settlement_.*"}
```

Find all latency metrics:
```promql
{__name__=~".*latency.*"}
```

Find all Stripe-related metrics:
```promql
{processor="stripe"}
```

Find error rate across all APIs:
```promql
sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m]))
```

---

## Retention & Archival
Real-time (hot): T=0 to T+15 days (SSD, Prometheus) Archive (cold): T+15 to T+365 (S3, queryable but slow) Long-term (frozen): T+365 to T+2555 (Glacier, restore only for audits)

**Prometheus keeps:** 15 days on SSD
**S3 keeps:** Everything, Glacier archives after 30 days
**Loki keeps:** 30 days hot, Glacier after

---

## Tools for Taxonomy Validation

```bash
# Check for high-cardinality metrics (in Python)
def check_cardinality(metric_name):
    # Query Prometheus API
    url = "http://prometheus:9090/api/v1/series"
    params = {"match[]": metric_name}
    response = requests.get(url, params=params)
    cardinality = len(response.json()['data'])
    
    if cardinality > 1000:
        print(f"⚠️ {metric_name} has {cardinality} combinations (high!)")
    else:
        print(f"✅ {metric_name} has {cardinality} combinations (ok)")
```
