FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY .python-version .
COPY README.md .

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
