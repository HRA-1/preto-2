FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_DEV_MODE=true

RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY jupyter_notebook_config.py /root/.jupyter/

EXPOSE 8501 8888

RUN chmod +x scripts/*.sh

CMD ["./scripts/start.sh"]
