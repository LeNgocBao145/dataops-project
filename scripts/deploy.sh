#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ENVIRONMENT=${1:-}
TARGET=${2:-}

if [ -z "$ENVIRONMENT" ] || [ -z "$TARGET" ]; then
    echo -e "${RED}Usage: ./deploy.sh <environment> <target>${NC}"
    echo "Example: ./deploy.sh test test"
    exit 1
fi

timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p logs backups
log_file="$(pwd)/logs/deploy_${ENVIRONMENT}_${timestamp}.log"

# Tee all output to deployment log file
exec > >(tee -a "$log_file") 2>&1

echo -e "${GREEN}🚀 Starting deployment to $ENVIRONMENT environment (target: $TARGET)...${NC}"
echo "Log file: $log_file"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Pre-deployment checks
echo -e "${YELLOW}📋 Running pre-deployment checks...${NC}"
cd dbt

echo "Installing DBT dependencies..."
dbt deps --target "$TARGET" --profiles-dir .

echo "Compiling DBT models..."
if ! dbt compile --target "$TARGET" --profiles-dir .; then
    echo -e "${RED}❌ Compilation failed${NC}"
    exit 1
fi

# 2. Backup current state
echo -e "${YELLOW}💾 Creating backup...${NC}"
backup_dir="../backups/${ENVIRONMENT}_${timestamp}"
mkdir -p "$backup_dir"
if [ -d "target" ]; then
    cp -r target/ "$backup_dir/"
fi
echo "Backup created at: $backup_dir"

# 3. Deploy models
echo -e "${YELLOW}🔨 Deploying models...${NC}"
if ! dbt run --target "$TARGET" --profiles-dir .; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# 4. Run post-deployment tests
echo -e "${YELLOW}✅ Running post-deployment tests...${NC}"
if ! dbt test --target "$TARGET" --profiles-dir .; then
    echo -e "${RED}❌ Post-deployment tests failed${NC}"
    exit 1
fi

# 5. Generate documentation
echo -e "${YELLOW}📚 Generating documentation...${NC}"
dbt docs generate --target "$TARGET" --profiles-dir .

# 6. Success message
echo -e "${GREEN}✨ Deployment to $ENVIRONMENT completed successfully!${NC}"
echo ""
echo "Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Target: $TARGET"
echo "  Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  Backup: $backup_dir"
echo "  Log: $log_file"
