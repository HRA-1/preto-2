#!/bin/bash

# Production start script
# Only runs Streamlit (no Jupyter Notebook for security and resource efficiency)

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set the PYTHONPATH to include the src directory
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/src"

# Disable development mode for production
export STREAMLIT_DEV_MODE=false

echo ""
echo "[PROD] Starting in PRODUCTION mode..."
echo "[PROD] Jupyter Notebook disabled for security"
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Start Streamlit app (production only)
echo "[PROD] Starting Streamlit app on port 8501..."
echo ""
echo "========================================"
echo "  Service is running:"
echo "  - Streamlit: http://localhost:8501"
echo "========================================"
echo ""

# Production-optimized Streamlit settings
exec streamlit run src/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
