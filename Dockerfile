FROM docker.io/library/python:3.10.8 AS base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

FROM base AS python-deps

COPY requirements.txt ./

RUN set -eux; \
    pip install --no-cache-dir pip-tools; \
    pip-sync requirements.txt --pip-args '--user'

FROM base

COPY --from=python-deps /root/.local /root/.local

WORKDIR /app
COPY . .

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]
CMD []