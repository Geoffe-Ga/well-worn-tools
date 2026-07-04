#!/usr/bin/env bash
set -euo pipefail

echo "=== Pre-deploy Checklist ==="

echo "1. Running backend tests..."
cd backend && source ../.venv/bin/activate
pytest --cov=. --cov-report=term-missing --cov-fail-under=90
echo "  Backend tests pass with >=90% coverage"

echo "2. Running frontend tests..."
cd ../frontend
npm test -- --watchAll=false
echo "  Frontend tests pass"

echo "3. Running pre-commit hooks..."
cd ..
pre-commit run --all-files
echo "  All pre-commit hooks pass"

echo "4. Building Docker images..."
# Build from the repo root — both Dockerfiles expect the repo root as the
# build context (matching most PaaS defaults when dockerfilePath is set).
docker build -f backend/Dockerfile -t backend-predeploy-check .
echo "  Backend Docker image builds successfully"
docker build -f frontend/Dockerfile -t frontend-predeploy-check .
echo "  Frontend Docker image builds successfully"

echo ""
echo "=== All checks passed. Ready to deploy! ==="
