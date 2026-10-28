.PHONY: help venv install-dev test lint sast dep-audit docker-build docker-scan sbom clean all

PYTHON   := python3
VENV     := .venv
BIN      := $(VENV)/bin
PYTEST   := $(BIN)/pytest
RUFF     := $(BIN)/ruff
BANDIT   := $(BIN)/bandit
AUDIT    := $(BIN)/pip-audit

IMAGE    := secure-supply-chain-app
TAG      := local

help:
	@echo "Targets: venv install-dev test lint sast dep-audit docker-build docker-scan sbom clean all"

venv:
	$(PYTHON) -m venv $(VENV)

install-dev: venv
	$(BIN)/pip install -e ".[dev]" -q

test: install-dev
	$(PYTEST) --cov=app --cov-report=term-missing

lint: install-dev
	$(RUFF) check src/ tests/
	$(RUFF) format --check src/ tests/

sast: install-dev
	$(BANDIT) -r src/ -f txt -ll

dep-audit: install-dev
	$(AUDIT)

docker-build:
	docker build --no-cache -t $(IMAGE):$(TAG) .
	@echo "Image built: $(IMAGE):$(TAG)"
	@docker images $(IMAGE):$(TAG)

docker-scan:
	@which trivy > /dev/null 2>&1 || (echo "trivy not installed — see https://aquasecurity.github.io/trivy/"; exit 1)
	trivy image --severity CRITICAL,HIGH $(IMAGE):$(TAG)

sbom:
	$(BIN)/pip install cyclonedx-bom -q
	$(BIN)/cyclonedx-py environment --output-format json --output-file sbom.json
	@echo "SBOM written to sbom.json"

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache htmlcov .coverage coverage.xml sbom.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

all: install-dev lint sast dep-audit test docker-build
