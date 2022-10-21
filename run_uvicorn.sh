clear
export OTEL_PYTHON_LOG_CORRELATION=true
uvicorn minimal_fastapi:app --reload --port 8080 --host 0.0.0.0