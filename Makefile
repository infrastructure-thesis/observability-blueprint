.PHONY: help setup lint test plan apply deploy clean

help:
    @echo "observability-blueprint: Common commands"
    @echo ""
    @echo "make setup           - Install dependencies"
    @echo "make lint            - Lint Terraform, K8s manifests, Python"
    @echo "make test            - Run tests"
    @echo "make plan            - Terraform plan (staging)"
    @echo "make apply           - Terraform apply (staging)"
    @echo "make deploy          - Deploy to staging"
    @echo "make clean           - Remove build artifacts"

setup:
    python3 -m venv venv
    . venv/bin/activate && pip install -r requirements-dev.txt

lint:
    terraform fmt -check -recursive terraform/
    python3 -m pytest tests/ -v --tb=short

test:
    python3 -m pytest tests/ -v --cov=. --cov-report=html

plan:
    cd terraform && terraform init && terraform plan -var="environment=staging"

apply:
    cd terraform && terraform apply -var="environment=staging"

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf .pytest_cache build dist *.egg-info

.DEFAULT_GOAL := help
