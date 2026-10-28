# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies only in builder stage
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir build \
 && python -m build --wheel --outdir /dist

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --gid 1001 appgroup \
 && useradd --uid 1001 --gid appgroup --no-create-home --shell /sbin/nologin appuser

WORKDIR /app

# Copy only the built wheel from builder — no build tools in runtime image
COPY --from=builder /dist/*.whl /tmp/

RUN pip install --no-cache-dir /tmp/*.whl \
 && rm /tmp/*.whl

# Drop to non-root
USER appuser

# No sensitive files, no shell history, no root
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

ENTRYPOINT ["verifier"]
CMD ["--help"]

# Labels for SBOM / supply chain traceability
LABEL org.opencontainers.image.title="secure-supply-chain-app" \
      org.opencontainers.image.description="File integrity verifier — supply chain demo" \
      org.opencontainers.image.source="https://github.com/aket0/secure-container-supply-chain" \
      org.opencontainers.image.licenses="MIT"
