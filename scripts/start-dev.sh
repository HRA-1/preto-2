#!/bin/bash

# Development start script
# Includes both Jupyter Notebook and Streamlit

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set the PYTHONPATH to include the src directory
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/src"

# Enable development mode
export STREAMLIT_DEV_MODE=true

echo ""
echo "[DEV] Starting in DEVELOPMENT mode..."
echo "[DEV] PYTHONPATH includes: ${PROJECT_ROOT}/src"
echo ""

# Change to project root
cd "${PROJECT_ROOT}"

# Start Jupyter Notebook in background
echo "[DEV] Starting Jupyter Notebook on port 8888..."
jupyter notebook --config=/root/.jupyter/jupyter_notebook_config.py &

# Give Jupyter a moment to start
sleep 2

# Start Streamlit app in foreground
echo "[DEV] Starting Streamlit app on port 8501..."
echo ""
echo "========================================"
echo "  Services are running:"
echo "  - Streamlit: http://localhost:8501"
echo "  - Jupyter:   http://localhost:8888"
echo "========================================"
echo ""

exec streamlit run src/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0
