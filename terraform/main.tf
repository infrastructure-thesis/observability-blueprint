# observability-blueprint: Production Terraform for AWS
# Deploy Prometheus + Grafana + Loki + Tempo on EKS
# Usage:
#   terraform init
#   terraform plan -var="environment=staging"
#   terraform apply

terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }

  # Uncomment for remote state (recommended)
  # backend "s3" {
  #   bucket         = "observability-blueprint-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

# ─────────────────────────────────────────────────────────
# VARIABLES
# ─────────────────────────────────────────────────────────

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "observability-blueprint"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

variable "replica_count" {
  description = "Number of replicas for HA"
  type        = number
  default     = 3
  validation {
    condition     = var.replica_count >= 1 && var.replica_count <= 10
    error_message = "Replica count must be between 1 and 10."
  }
}

variable "fintech_region" {
  description = "AWS region for fintech data residency (GDPR: must be eu-*)"
  type        = string
  default     = "us-east-1"
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization (spot instances, auto-scaling)"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention (days)"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Must be a valid CloudWatch retention period."
  }
}

variable "enable_encryption" {
  description = "Enable encryption at rest (KMS) and in transit (TLS)"
  type        = bool
  default     = true
}

# ─────────────────────────────────────────────────────────
# PROVIDERS
# ─────────────────────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "observability-blueprint"
      ManagedBy   = "terraform"
      CostCenter  = "platform-engineering"
    }
  }
}

provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.main.token
  }
}

data "aws_eks_cluster_auth" "main" {
  name = aws_eks_cluster.main.name
}

# ─────────────────────────────────────────────────────────
# VPC & NETWORKING
# ─────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 101}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.cluster_name}-private-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.cluster_name}-igw"
  }
}

resource "aws_eip" "nat" {
  count  = 3
  domain = "vpc"

  tags = {
    Name = "${var.cluster_name}-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count         = 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.cluster_name}-nat-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.cluster_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 3
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  count  = 3
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.cluster_name}-private-rt-${count.index + 1}"
  }
}

resource "aws_route_table_association" "private" {
  count          = 3
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ─────────────────────────────────────────────────────────
# EKS CLUSTER
# ─────────────────────────────────────────────────────────

resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
}

resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.kubernetes_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  # Enable control plane logging
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = {
    Name = var.cluster_name
  }
}

# ─────────────────────────────────────────────────────────
# EKS NODE GROUPS
# ─────────────────────────────────────────────────────────

resource "aws_iam_role" "eks_nodes" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  role       = aws_iam_role.eks_nodes.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  role       = aws_iam_role.eks_nodes.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "eks_registry_policy" {
  role       = aws_iam_role.eks_nodes.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {
    desired_size = var.replica_count
    max_size     = var.replica_count * 2
    min_size     = var.replica_count
  }

  instance_types = [
    var.environment == "dev" ? "t3.large" : "t3.xlarge"
  ]

  # Use spot instances for cost optimization
  capacity_type = var.enable_cost_optimization ? "SPOT" : "ON_DEMAND"

  disk_size = 100

  tags = {
    Name = "${var.cluster_name}-nodes"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_registry_policy,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# ─────────────────────────────────────────────────────────
# S3 BUCKETS (Log & Metric Storage)
# ─────────────────────────────────────────────────────────

resource "aws_s3_bucket" "observability_logs" {
  bucket = "${var.cluster_name}-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.cluster_name}-logs"
  }
}

resource "aws_s3_bucket_versioning" "observability_logs" {
  bucket = aws_s3_bucket.observability_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "observability_logs" {
  bucket = aws_s3_bucket.observability_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = var.enable_encryption ? "aws:kms" : "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "observability_logs" {
  bucket = aws_s3_bucket.observability_logs.id

  rule {
    id     = "archive-old-logs"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365  # Delete after 1 year
    }
  }
}

resource "aws_s3_bucket_public_access_block" "observability_logs" {
  bucket = aws_s3_bucket.observability_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ─────────────────────────────────────────────────────────
# RDS (Grafana Database - Optional)
# ─────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "grafana" {
  name       = "${var.cluster_name}-grafana"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.cluster_name}-grafana-subnet-group"
  }
}

resource "aws_rds_cluster" "grafana" {
  count              = var.environment == "prod" ? 1 : 0
  cluster_identifier = "${var.cluster_name}-grafana"
  engine             = "aurora-postgresql"
  engine_version     = "14.6"
  database_name      = "grafana"
  master_username    = "grafana_admin"
  master_password    = random_password.grafana_db.result
  port               = 5432

  db_subnet_group_name            = aws_db_subnet_group.grafana.name
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.grafana[0].name
  skip_final_snapshot             = var.environment != "prod"
  backup_retention_period         = var.environment == "prod" ? 30 : 7
  storage_encrypted               = var.enable_encryption

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "${var.cluster_name}-grafana-db"
  }
}

resource "aws_rds_cluster_parameter_group" "grafana" {
  count  = var.environment == "prod" ? 1 : 0
  name   = "${var.cluster_name}-grafana"
  family = "aurora-postgresql14"

  parameter {
    name  = "ssl"
    value = "1"
  }
}

resource "random_password" "grafana_db" {
  length  = 32
  special = true
}

# ─────────────────────────────────────────────────────────
# NAMESPACES & RBAC
# ─────────────────────────────────────────────────────────

resource "kubernetes_namespace" "observability" {
  metadata {
    name = "observability"

    labels = {
      "app.kubernetes.io/name"       = "observability-blueprint"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  depends_on = [aws_eks_cluster.main]
}

# Service Account for Prometheus (for IAM permissions)
resource "kubernetes_service_account" "prometheus" {
  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.observability.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.prometheus.arn
    }
  }
}

resource "aws_iam_role" "prometheus" {
  name = "${var.cluster_name}-prometheus-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:observability:prometheus"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "prometheus" {
  name = "${var.cluster_name}-prometheus-policy"
  role = aws_iam_role.prometheus.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.observability_logs.arn,
          "${aws_s3_bucket.observability_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags",
          "ec2:DescribeNetworkInterfaces"
        ]
        Resource = "*"
      }
    ]
  })
}

# ─────────────────────────────────────────────────────────
# HELM DEPLOYMENT (observability stack)
# ─────────────────────────────────────────────────────────

# Add Prometheus Helm repo
resource "helm_repository" "prometheus" {
  name = "prometheus-community"
  url  = "https://prometheus-community.github.io/helm-charts"
}

# Add Grafana Helm repo
resource "helm_repository" "grafana" {
  name = "grafana"
  url  = "https://grafana.github.io/helm-charts"
}

# Deploy Prometheus
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = helm_repository.prometheus.name
  chart      = "kube-prometheus-stack"
  version    = "51.3.0"
  namespace  = kubernetes_namespace.observability.metadata[0].name

  values = [
    yamlencode({
      prometheus = {
        prometheusSpec = {
          replicas    = var.replica_count
          retention   = "15d"
          retentionSize = "50GB"
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                accessModes = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.environment == "prod" ? "100Gi" : "50Gi"
                  }
                }
              }
            }
          }
          resources = {
            requests = {
              cpu    = "500m"
              memory = "2Gi"
            }
            limits = {
              cpu    = "2000m"
              memory = "4Gi"
            }
          }

          # S3 remote write (for long-term storage)
          remoteWrite = [
            {
              url = "http://minio:9000/api/v1/prom/write"
              # Configure for your S3-compatible storage
            }
          ]

          # Service monitor selectors
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues     = false
        }

        # Alert manager
        alertmanager = {
          alertmanagerSpec = {
            replicas = var.replica_count
            storage = {
              volumeClaimTemplate = {
                spec = {
                  accessModes = ["ReadWriteOnce"]
                  resources = {
                    requests = {
                      storage = "10Gi"
                    }
                  }
                }
              }
            }
          }
        }
      }

      # Grafana
      grafana = {
        replicas = var.replica_count
        persistence = {
          enabled = true
          size    = "10Gi"
        }
        datasources = {
          "datasources.yaml" = {
            apiVersion = 1
            datasources = [
              {
                name      = "Prometheus"
                type      = "prometheus"
                url       = "http://prometheus-operated:9090"
                isDefault = true
              }
            ]
          }
        }
      }

      # Prometheus Node Exporter
      prometheus-node-exporter = {
        tolerations = [
          {
            operator = "Exists"
          }
        ]
      }
    })
  ]

  depends_on = [
    aws_eks_node_group.main,
    kubernetes_namespace.observability
  ]
}

# Deploy Loki (Log Aggregation)
resource "helm_release" "loki" {
  name       = "loki"
  repository = helm_repository.grafana.name
  chart      = "loki-stack"
  version    = "2.9.3"
  namespace  = kubernetes_namespace.observability.metadata[0].name

  values = [
    yamlencode({
      loki = {
        enabled = true
        config = {
          auth_enabled = false
          ingester = {
            chunk_idle_period = "3m"
            max_chunk_age     = "1h"
          }
          schema_config = {
            configs = [
              {
                from       = "2020-10-24"
                store      = "boltdb-shipper"
                object_store = "s3"
                schema     = "v11"
                index = {
                  prefix = "index_"
                  period = "24h"
                }
              }
            ]
          }
          storage_config = {
            s3 = {
              s3       = "s3://${var.aws_region}/${aws_s3_bucket.observability_logs.bucket}/loki"
              endpoint = "s3.${var.aws_region}.amazonaws.com"
            }
          }
        }
      }

      promtail = {
        enabled = true
      }
    })
  ]

  depends_on = [
    helm_release.prometheus,
    aws_s3_bucket.observability_logs
  ]
}

# ─────────────────────────────────────────────────────────
# CloudWatch Alarms (Infrastructure Monitoring)
# ─────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "eks_node_cpu" {
  alarm_name          = "${var.cluster_name}-eks-node-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when EKS node CPU exceeds 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = aws_eks_node_group.main.resources[0].autoscaling_groups[0].name
  }
}

resource "aws_sns_topic" "alerts" {
  name = "${var.cluster_name}-alerts"

  kms_master_key_id = var.enable_encryption ? "alias/aws/sns" : null
}

# ─────────────────────────────────────────────────────────
# OUTPUTS
# ─────────────────────────────────────────────────────────

data "aws_caller_identity" "current" {}

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "EKS cluster API endpoint"
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "EKS cluster name"
}

output "prometheus_url" {
  value       = "http://prometheus-operated.observability.svc.cluster.local:9090"
  description = "Prometheus URL (internal)"
}

output "grafana_url" {
  value       = "http://prometheus-grafana.observability.svc.cluster.local:80"
  description = "Grafana URL (internal, expose via port-forward)"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.observability_logs.bucket
  description = "S3 bucket for logs and long-term storage"
}

output "cost_estimate" {
  value       = "Monthly cost estimate: $${var.replica_count * 150} (varies by region)"
  description = "Approximate monthly infrastructure cost"
}

output "kubectl_config" {
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
  description = "Command to configure kubectl"
}

output "grafana_port_forward" {
  value       = "kubectl port-forward -n observability svc/prometheus-grafana 3000:80"
  description = "Command to access Grafana locally"
}

# ─────────────────────────────────────────────────────────
# LOCALS (Computed Values)
# ─────────────────────────────────────────────────────────

locals {
  environment_config = {
    dev = {
      instance_type       = "t3.large"
      replicas            = 1
      retention_days      = 7
      backup_retention    = 1
    }
    staging = {
      instance_type       = "t3.xlarge"
      replicas            = 2
      retention_days      = 30
      backup_retention    = 7
    }
    prod = {
      instance_type       = "t3.2xlarge"
      replicas            = 3
      retention_days      = 90
      backup_retention    = 30
    }
  }

  cluster_config = local.environment_config[var.environment]
}
