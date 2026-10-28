# secure-container-supply-chain

A containerized Python application built through a secure software supply chain.

## Problem Solved

Container images are complex artifacts with many potential attack vectors: bloated base images,
root execution, embedded secrets, unverified dependencies, and unsigned artifacts. This project
demonstrates how to build and ship a production-ready container with defense-in-depth at every
step of the supply chain.

## Architecture

```
secure-container-supply-chain/
├── src/app/
│   ├── verifier.py     # File integrity verifier (SHA-256)
│   └── cli.py          # CLI entry point
├── tests/
│   ├── test_verifier.py    # Unit + integration tests
│   └── test_cli.py         # CLI tests
├── Dockerfile              # Multi-stage build
├── .dockerignore
├── .github/workflows/
│   └── supply-chain.yml    # Full supply chain pipeline
└── docs/
    ├── signing.md              # Cosign signing procedure
    └── supply-chain-security.md  # Controls & trust model
```

### Docker: Multi-stage Build

```
python:3.12-slim (builder)
  └── pip install build
  └── python -m build → .whl
        ↓
python:3.12-slim (runtime)
  └── pip install .whl
  └── USER appuser (non-root, UID 1001)
  └── ENTRYPOINT ["verifier"]
```

## Technologies

| Tool / Standard     | Purpose                                |
|---------------------|----------------------------------------|
| Python 3.12         | Application language                   |
| Docker multi-stage  | Minimal image, no build tools at runtime |
| pytest              | Unit and integration tests             |
| ruff / bandit       | Lint + SAST                            |
| pip-audit           | Dependency CVE scan                    |
| Trivy               | Image CVE scan (in GitHub Actions)     |
| CycloneDX           | SBOM generation                        |
| Cosign (Sigstore)   | Keyless artifact signing               |

## Prerequisites

- Python 3.11+ (for local dev)
- Docker (for image build)
- `make` (optional)

## Installation (local dev)

```bash
git clone https://github.com/aket0/secure-container-supply-chain.git
cd secure-container-supply-chain

make install-dev
# or:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
make test
# or: pytest --cov=app --cov-report=term-missing
```

Expected: all tests pass, coverage ≥ 80%.

## Docker Build (local)

```bash
make docker-build
# or:
docker build -t secure-supply-chain-app:local .

# Run the tool
docker run --rm secure-supply-chain-app:local hash /dev/null
docker run --rm -v $(pwd):/data secure-supply-chain-app:local \
  verify /data/manifest.json --base-dir /data
```

## Security Controls

### Image Security
- Multi-stage build: runtime image has no compiler, no pip, no shell scripts
- Non-root user: UID/GID 1001, no home directory, no shell
- Read-only filesystem compatible (`/tmp` for ephemeral writes)
- `.dockerignore` excludes tests, docs, caches, and secret-adjacent files

### Supply Chain Controls

| Control              | Where                   | Status                    |
|----------------------|-------------------------|---------------------------|
| Dependency audit     | pip-audit (CI)          | Validated                 |
| Image scan           | Trivy (CI)              | Validated in Actions      |
| SBOM generation      | CycloneDX (CI)          | Validated in Actions      |
| Artifact signing     | Cosign keyless (CI)     | Ready — needs registry    |
| Secret detection     | gitleaks (CI)           | Validated in Actions      |

## Observed Results (local)

```bash
make test       # all tests pass, coverage ≥ 80%
make docker-build  # image built, non-root verified
docker inspect secure-supply-chain-app:local | grep -i user
# → "User": "appuser"
```

## Known Limits

- Trivy, CycloneDX, and Cosign are not installed locally; they run in GitHub Actions.
- Cosign signing requires a registry push with a digest reference. The workflow is defined
  and ready — see `docs/signing.md`.
- SLSA provenance (level 2+) is documented as an improvement path, not yet implemented.
- The base image (`python:3.12-slim`) receives periodic CVE updates from upstream.
  Rebuild regularly.

## Improvement Paths

- Add SLSA provenance via `slsa-framework/slsa-github-generator`.
- Pin action versions to commit SHAs.
- Switch to a distroless base image.
- Automate base image rebuild on upstream CVE alerts (Dependabot / Renovate).
- Sign the SBOM itself.
