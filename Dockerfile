FROM docker.io/library/python:3.10.8

COPY requirements.txt ./

RUN set -eux; \
    pip install --no-cache-dir pip-tools; \
    pip-sync requirements.txt

WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]
CMD []