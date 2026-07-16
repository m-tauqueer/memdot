# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir "uv==0.11.28"
COPY packages/domain-python ./packages/domain-python
COPY services/workers ./services/workers
RUN uv pip install --system --no-cache ./packages/domain-python \
  && uv pip install --system --no-cache --no-sources ./services/workers

FROM python:3.12-slim AS runner
ARG MEMDOT_SOURCE_HASH=unknown
LABEL memdot.source_hash=$MEMDOT_SOURCE_HASH
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin memdot
WORKDIR /app
ENV WORKERS_ENV=production
ENV WORKERS_HEALTH_HOST=0.0.0.0
ENV WORKERS_HEALTH_PORT=8300
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
USER 10001
EXPOSE 8300
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8300/health/live')"
CMD ["memdot-workers"]
