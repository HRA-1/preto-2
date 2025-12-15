#!/bin/bash
set -e

ENVIRONMENT=${ENVIRONMENT:-dev}

echo "Starting in $ENVIRONMENT mode..."

if [ "$ENVIRONMENT" = "prod" ]; then
    exec ./scripts/start-prod.sh
else
    exec ./scripts/start-dev.sh
fi
