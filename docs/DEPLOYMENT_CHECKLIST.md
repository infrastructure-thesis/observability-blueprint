# observability-blueprint: Production Deployment Checklist

**Purpose:** Verify production readiness before going live. All items must be completed.

---

## PRE-DEPLOYMENT (Week Before)

### Infrastructure Planning
- [ ] **Resource Sizing**
  - [ ] Prometheus storage: Calculate for 15-day retention
    - Formula: `(metrics_per_second × 86400 × 15) / compression_ratio`
    - Typical: 2GB/day → 30GB SSD needed
  - [ ] Loki storage: Calculate for 30-day retention
    - Formula: `(logs_gb_per_day × 30) + 20% overhead`
    - Typical: 100GB/day → 3TB S3 storage
  - [ ] Grafana database: Minimum 20GB RDS instance
  - [ ] EKS cluster: Minimum 3 t3.xlarge nodes (HA)

- [ ] **Network Planning**
  - [ ] VPC CIDR blocks: `10.0.0.0/16` (no overlap with existing)
  - [ ] Public subnets: 3 availability zones (min 2)
  - [ ] Private subnets: 3 availability zones (min 2)
  - [ ] NAT gateways: 1 per AZ (cost: $32/month each)
  - [ ] Network policies: Zero-trust (deny all, allow specific)

- [ ] **Disaster Recovery**
  - [ ] Backup strategy: Daily automated snapshots
  - [ ] RPO (Recovery Point Objective): <1 hour
  - [ ] RTO (Recovery Time Objective): <2 hours
  - [ ] Tested recovery process: Simulate restore from backup

### Security Pre-Check
- [ ] **Encryption**
  - [ ] KMS key created + rotation enabled
  - [ ] S3 buckets encrypted with KMS
  - [ ] RDS encryption enabled
  - [ ] EBS volumes encrypted
  - [ ] TLS 1.3 configured for all APIs

- [ ] **Access Control**
  - [ ] IAM roles created (least privilege)
  - [ ] Service accounts created with IAM role-to-pod bindings
  - [ ] OIDC provider configured (SSO/SAML)
  - [ ] RBAC policies applied (namespace-level)
  - [ ] Pod security policies enabled (no root containers)

- [ ] **Secrets Management**
  - [ ] Grafana admin password: Generated, stored in AWS Secrets Manager
  - [ ] Database credentials: Rotated, stored in AWS Secrets Manager
  - [ ] API tokens: Rotated, no hardcoded values
  - [ ] Verification: `grep -r "password\|api_key\|secret" . --include="*.yaml" --include="*.json"` (should return 0)

### Cost Estimation
- [ ] **Run Infracost**
  ```bash
  infracost breakdown --path terraform/
  ```
  Expected cost ranges:
  - Dev: $300-500/month
  - Staging: $800-1,200/month
  - Prod: $1,500-2,500/month

- [ ] **Budget Alert Configured**
  ```bash
  aws budgets create-budget \
    --account-id [ACCOUNT_ID] \
    --budget "Name=Observability,Type=MONTHLY,Limit=2500"
  ```

---

## DEPLOYMENT (Day 0)

### Phase 1: Infrastructure (Hour 0-2)

```bash
# 1. Initialize Terraform
cd terraform
terraform init

# 2. Validate configuration
terraform validate
terraform fmt -check

# 3. Plan deployment (review before apply)
terraform plan \
  -var="environment=prod" \
  -var="replica_count=3" \
  -out=tfplan

# 4. Apply infrastructure
terraform apply tfplan

# 5. Verify outputs
terraform output
# Expected:
# - eks_cluster_endpoint: https://...
# - eks_cluster_name: observability-blueprint-prod
# - prometheus_url: http://prometheus-operated.observability:9090
# - grafana_url: http://prometheus-grafana.observability:80
```

### Phase 2: Kubernetes Setup (Hour 2-3)

```bash
# 1. Update kubeconfig
aws eks update-kubeconfig \
  --name observability-blueprint \
  --region us-east-1

# 2. Verify cluster access
kubectl get nodes
# Expected: 3 nodes in READY state

# 3. Create namespaces
kubectl create namespace observability
kubectl create namespace monitoring

# 4. Label nodes for workload placement
kubectl label nodes \
  -l NodeGroup=observability-blueprint-nodes \
  workload=monitoring
```

### Phase 3: Secrets & Configuration (Hour 3-4)

```bash
# 1. Create secrets
kubectl create secret generic grafana-admin \
  --from-literal=admin-password=$(openssl rand -base64 32) \
  -n observability

kubectl create secret generic prometheus-config \
  --from-file=prometheus.yml=./configs/prometheus.yml \
  -n observability

# 2. Verify secrets (non-sensitive fields)
kubectl describe secret grafana-admin -n observability
# Should show: admin-password (no value shown)

# 3. Create config maps
kubectl create configmap alert-rules \
  --from-file=./alerts/ \
  -n observability
```

### Phase 4: Deploy Observability Stack (Hour 4-5)

```bash
# 1. Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# 2. Deploy Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  -f helm/values-prod.yaml \
  -n observability \
  --timeout 10m

# 3. Deploy Loki
helm install loki grafana/loki-stack \
  -f helm/loki-prod.yaml \
  -n observability

# 4. Wait for pods
kubectl wait --for=condition=ready pod \
  -l app=prometheus,app=grafana,app=loki \
  -n observability --timeout=600s
```

### Phase 5: Verification (Hour 5-6)

```bash
# 1. Check pod status
kubectl get pods -n observability
# Expected: All pods RUNNING

# 2. Verify Prometheus scraping
kubectl port-forward svc/prometheus 9090:9090 -n observability &
curl http://localhost:9090/api/v1/targets
# Expected: All scrape targets "healthy"

# 3. Verify Grafana dashboards
kubectl port-forward svc/prometheus-grafana 3000:80 -n observability &
curl http://localhost:3000/api/health
# Expected: {"ok": true}

# 4. Load test dashboards
for dashboard in dashboards/*.json; do
  curl -X POST http://localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @$dashboard
done

# 5. Verify alerts
kubectl logs -n observability alertmanager-* | grep "routes configured"
```

---

## POST-DEPLOYMENT (Day 1-7)

### Day 1: Smoke Tests

- [ ] **Metrics Collection**
  ```bash
  # Verify Prometheus is scraping
  kubectl exec -it prometheus-0 -n observability -- \
    curl http://localhost:9090/api/v1/query?query=up | jq '.data.result | length'
  # Expected: >50 (multiple targets healthy)
  ```

- [ ] **Log Ingestion**
  ```bash
  # Verify Loki is receiving logs
  kubectl exec -it loki-0 -n observability -- \
    curl http://localhost:3100/loki/api/v1/labels
  # Expected: Labels like job, pod, namespace
  ```

- [ ] **Dashboard Loading**
  - [ ] "Settlement Health" dashboard loads within 2 seconds
  - [ ] "Compliance Drift" dashboard has data
  - [ ] "Cost Intelligence" dashboard shows metrics

- [ ] **Alerts Firing**
  - [ ] Manually trigger test alert:
    ```bash
    # High CPU test
    kubectl exec -it prometheus-0 -n observability -- \
      stress-ng --cpu 4 --timeout 60s
    
    # Verify alert fires
    curl http://localhost:9090/api/v1/alerts | jq '.data.alerts | length'
    ```

### Day 2: Integration Testing

- [ ] **Data Pipeline**
  - [ ] Prometheus → Grafana datasource connection
  - [ ] Loki → Grafana datasource connection
  - [ ] Tempo → Grafana datasource connection
  - [ ] Test query: `sum(rate(http_request_total[5m]))`

- [ ] **Alert Routing**
  - [ ] Critical alerts → PagerDuty (test)
  - [ ] Warning alerts → Slack (test)
  - [ ] Info alerts → Email digest (test)

- [ ] **Retention Policies**
  - [ ] Prometheus deletion after 15 days
  - [ ] Loki archival to S3 after 30 days
  - [ ] S3 lifecycle rule to Glacier after 90 days

### Day 3-4: Load Testing

- [ ] **Metrics Volume**
  ```bash
  # Load 1M metrics into Prometheus
  python scripts/load_test_metrics.py --count=1000000
  
  # Verify Prometheus handles volume
  curl http://localhost:9090/api/v1/query?query=topk(10,up) | jq '.data.result | length'
  # Expected: 10 (no slowdown)
  ```

- [ ] **Query Performance**
  ```bash
  # Run benchmark queries
  python scripts/benchmark_queries.py
  # Expected P95 latency: <200ms
  ```

- [ ] **Dashboard Performance**
  - [ ] All dashboards load in <3 seconds
  - [ ] 10 concurrent users browsing dashboards (no errors)

### Day 5-7: Production Validation

- [ ] **Backup Verification**
  ```bash
  # Test backup restoration
  ./scripts/test_backup_restore.sh
  # Expected: Can restore Prometheus data from backup
  ```

- [ ] **Failover Testing**
  ```bash
  # Simulate pod failure
  kubectl delete pod prometheus-0 -n observability
  
  # Verify Prometheus recovers
  kubectl get pod -n observability | grep prometheus
  # Expected: New pod created, running within 30s
  ```

- [ ] **Security Scan**
  ```bash
  # Run Trivy security scan
  trivy image prometheus:latest
  # Expected: 0 critical vulnerabilities
  ```

- [ ] **Compliance Check**
  ```bash
  # Run compliance validator
  ./scripts/compliance_check.sh prod
  # Expected: ✅ All checks pass
  ```

---

## ONGOING OPERATIONS

### Weekly Tasks
- [ ] **Backup Verification**
  ```bash
  # Verify daily backups completed
  aws s3 ls s3://observability-blueprint-backups/$(date +%Y-%m)/ | wc -l
  # Expected: ≥7 (one per day)
  ```

- [ ] **Disk Space Monitoring**
  ```bash
  # Check Prometheus storage
  kubectl exec -it prometheus-0 -n observability -- df -h /prometheus
  # Expected: <80% full
  
  # Check Loki storage
  kubectl exec -it loki-0 -n observability -- df -h /loki
  # Expected: <80% full
  ```

### Monthly Tasks
- [ ] **Update Helm Charts**
  ```bash
  helm repo update
  helm upgrade prometheus prometheus-community/kube-prometheus-stack \
    -f helm/values-prod.yaml -n observability
  ```

- [ ] **Rotate Secrets**
  ```bash
  # Rotate Grafana admin password
  kubectl create secret generic grafana-admin \
    --from-literal=admin-password=$(openssl rand -base64 32) \
    -n observability --dry-run=client -o yaml | kubectl apply -f -
  ```

- [ ] **Security Patching**
  ```bash
  # Update container images
  trivy image --severity HIGH,CRITICAL prometheus:* grafana:* loki:*
  # Apply patches for any CVEs found
  ```

### Quarterly Tasks
- [ ] **Performance Tuning**
  - [ ] Review slow query logs
  - [ ] Optimize high-cardinality metrics
  - [ ] Adjust retention policies

- [ ] **Compliance Audit**
  ```bash
  # Generate compliance report
  ./scripts/compliance_audit.sh prod
  # Export for auditor review
  ```

- [ ] **Cost Review**
  ```bash
  # Analyze spending trends
  aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-03-31 \
    --granularity MONTHLY \
    --metrics BlendedCost
  ```

---

## Rollback Procedure (If Needed)

**Time to Rollback:** <15 minutes

```bash
# 1. Identify issue
kubectl logs -n observability prometheus-* --tail=100 | grep ERROR

# 2. Rollback Helm release
helm rollback prometheus 1 -n observability
# Expected: Previous version restored

# 3. Verify metrics flowing
kubectl exec -it prometheus-0 -n observability -- \
  curl http://localhost:9090/api/v1/labels

# 4. Re-alert team
echo "Rollback complete, metrics flowing" | \
  curl -X POST -d @- https://hooks.slack.com/[webhook-url]
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Platform Engineer** | | | |
| **Security Lead** | | | |
| **Compliance Officer** | | | |
| **Finance/Cost Owner** | | | |

---

## Post-Deployment Communication

**Email to Stakeholders:**
```
Subject: observability-blueprint Deployed to Production ✅

Team,

Observability stack is now live in production:
- Prometheus: http://prometheus-operated.observability:9090
- Grafana: http://prometheus-grafana.observability:80 (via port-forward)
- Alert routing: Critical → PagerDuty | Warnings → Slack

Key dashboards:
1. Settlement Health (for trading ops)
2. Compliance Drift (for compliance team)
3. Cost Intelligence (for finance)

On-call runbooks available at: docs/RUNBOOKS.md
Compliance evidence: compliance/compliance-audit-[DATE].json

Questions? Reach out in #observability-support
```

---

**Last Updated:** [Today's Date]
**Next Review:** 30 days post-deployment
