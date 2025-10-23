FROM python:3.12-slim

RUN mkdir /code && \
    apt update && \
    apt install -y --no-install-recommends unzip vim zip && \
    apt clean && \
    pip install --upgrade pip && \
    pip install uv && \
    adduser marktech

USER marktech


ENV PYTHONUNBUFFERED=1
WORKDIR /home/marktech/
COPY pyproject.toml ./
RUN uv sync

COPY --chown=marktech:marktech ./src/ .
ENV PORT=${PORT:-8000}
EXPOSE ${PORT}
CMD ["sh", "./backend-entrypoint.sh"]
