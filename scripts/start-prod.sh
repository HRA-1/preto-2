#!/bin/bash
set -e

echo "Starting production environment..."

# Only run Streamlit in production (no Jupyter for security)
echo "Starting Streamlit on port 8501..."
exec streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
