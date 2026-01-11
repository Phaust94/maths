# Base stage for installing uv
FROM python:3.13-slim as base
RUN pip install uv

# Builder stage for installing dependencies
FROM base as builder
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system -r pyproject.toml

# Final stage
FROM python:3.13-slim as final
WORKDIR /app
COPY --from=builder /root/.cache/uv /root/.cache/uv
COPY . .

CMD ["python", "main.py"]
