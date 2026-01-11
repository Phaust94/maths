# Base stage for installing uv
FROM python:3.13-slim as base
RUN pip install uv

# Builder stage for installing dependencies
FROM base as builder
WORKDIR /app
COPY pyproject.toml ./
RUN uv venv
RUN . .venv/bin/activate && uv pip install .

# Final stage
FROM python:3.13-slim as final
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY . .

CMD [".venv/bin/python", "main.py"]
