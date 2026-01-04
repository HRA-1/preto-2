FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_DEV_MODE=true

RUN apt-get update && apt-get install -y \
    procps \
    dos2unix \
    fonts-nanum \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN rm -rf ~/.cache/matplotlib

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY . .
COPY jupyter_notebook_config.py /root/.jupyter/

EXPOSE 8501 8888

# Convert line endings (for Windows compatibility) and set execute permission
RUN dos2unix scripts/*.sh && chmod +x scripts/*.sh

CMD ["./scripts/start.sh"]
