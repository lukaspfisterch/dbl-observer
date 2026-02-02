FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN pip install --no-cache-dir -U pip

# Copy + install
COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir -e .

EXPOSE 8020

# Start Observer Server
# Assuming dbl-observer-server is installed as a script
CMD ["dbl-observer-server", "--host", "0.0.0.0", "--port", "8020"]
