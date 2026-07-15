# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir "uv==0.11.28"
COPY packages/domain-python ./packages/domain-python
COPY services/core ./services/core
RUN uv pip install --system --no-cache ./packages/domain-python \
  && uv pip install --system --no-cache --no-sources ./services/core

FROM python:3.12-slim AS runner
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin memdot
WORKDIR /app
ENV CORE_ENV=production
ENV CORE_HOST=0.0.0.0
ENV CORE_PORT=8000
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')"
CMD ["memdot-core"]
