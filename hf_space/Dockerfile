FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.frontend.txt ./
RUN pip install --no-cache-dir -r requirements.frontend.txt

COPY frontend/ ./frontend/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# BACKEND_URL is set as a Space secret pointing to the AMD VM backend
ENV BACKEND_URL=${BACKEND_URL}

EXPOSE 7860

CMD ["streamlit", "run", "frontend/app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
