#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-}
BACKUP_DIR=${2:-}
AUTO_CONFIRM=false
TARGET=""

# Parse optional flags/target
shift $(( $# >= 2 ? 2 : $# )) || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

if [ -z "$ENVIRONMENT" ] || [ -z "$BACKUP_DIR" ]; then
    echo -e "${RED}Usage: ./rollback.sh <environment> <backup_directory> [target] [-y|--yes]${NC}"
    echo "Example: ./rollback.sh production backups/production_20260101_120000 prod --yes"
    exit 1
fi

# Map environment name to dbt profile target when not explicitly provided
if [ -z "$TARGET" ]; then
    case "$ENVIRONMENT" in
        production|prod) TARGET="prod" ;;
        development|dev) TARGET="dev" ;;
        *) TARGET="$ENVIRONMENT" ;;
    esac
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will rollback to a previous state${NC}"
echo "Environment: $ENVIRONMENT"
echo "Target: $TARGET"
echo "Backup: $BACKUP_DIR"
echo ""

if [ "$AUTO_CONFIRM" != true ]; then
    read -r -p "Are you sure you want to proceed? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Rollback cancelled"
        exit 0
    fi
fi

echo -e "${GREEN}🔄 Starting rollback...${NC}"

# Restore backup
echo "Restoring from backup..."
BACKUP_ABS=$(cd "$BACKUP_DIR" && pwd)
cd dbt
rm -rf target/
if [ -d "$BACKUP_ABS/target" ]; then
    cp -r "$BACKUP_ABS/target" ./target
else
    cp -r "$BACKUP_ABS" ./target
fi

# Re-run models from backup state
echo "Re-deploying previous state (target: $TARGET)..."
if ! dbt run --target "$TARGET" --profiles-dir .; then
    echo -e "${RED}❌ Rollback failed${NC}"
    exit 1
fi

# Run tests
echo "Running tests..."
if ! dbt test --target "$TARGET" --profiles-dir .; then
    echo -e "${RED}❌ Rollback validation tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Rollback completed successfully${NC}"
