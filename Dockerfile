FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/cache/huggingface
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY app ./app
COPY configs ./configs
COPY scripts ./scripts
COPY docs ./docs
COPY data ./data
COPY tests ./tests

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e . --no-deps \
    && python -m pip install \
        pyyaml \
        pydantic \
        pytest \
        streamlit \
        python-dotenv \
        "transformers>=4.51.0,<5" \
        accelerate \
        langchain-community \
        "mmore[index,rag]==1.2.2" \
        "docker==7.1.0" \
        faiss-cpu

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
