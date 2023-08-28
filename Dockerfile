FROM docker.io/library/python:3.11.5 as base

ARG APP_VERSION=0.0.0
ARG APP_COMMIT=0000000000

ENV PYTHONUNBUFFERED=1

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Setup build environment
RUN pip install poetry
RUN python -m venv /venv

# Install python dependencies into virtual environment
COPY pyproject.toml poetry.lock ./
RUN . /venv/bin/activate && poetry install --sync --without dev --no-root

FROM base as final

# Copy python dependencies
COPY --from=builder /venv /venv

# Copy application files
WORKDIR /app
COPY . .

# Add application version/commit info
RUN echo "VERSION = '$APP_VERSION' \nCOMMIT = '$(echo $APP_COMMIT | head -c 10)'" > version.py

# Set entrypoint
RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]
CMD []
