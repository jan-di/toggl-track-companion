FROM docker.io/library/python:3.11.4

ARG APP_VERSION=0.0.0
ARG APP_COMMIT=0000000000

COPY requirements.txt ./

RUN set -eux; \
    pip install --no-cache-dir pip-tools; \
    pip-sync requirements.txt

WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1

RUN echo "VERSION = '$APP_VERSION' \nCOMMIT = '$(echo $APP_COMMIT | head -c 10)'" > version.py

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]
CMD []