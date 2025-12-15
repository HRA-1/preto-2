#!/bin/bash
set -e

echo "Starting development environment..."

# Start Jupyter Notebook in background
echo "Starting Jupyter Notebook on port 8888..."
jupyter notebook --config=/root/.jupyter/jupyter_notebook_config.py &

# Start Streamlit in foreground
echo "Starting Streamlit on port 8501..."
exec streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
