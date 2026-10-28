# Supply Chain Security

## Controls Implemented

### 1. Multi-stage Docker Build

- **Builder stage**: installs build tools, compiles wheel
- **Runtime stage**: copies only the wheel; no compiler, no pip, no build tools
- Result: minimal attack surface in the final image

### 2. Non-root User

The runtime image runs as `appuser` (UID 1001, GID 1001).
No shell, no home directory, no write access outside `/tmp`.

### 3. Minimal Base Image

`python:3.12-slim` — Debian slim variant.
Only runtime Python libraries are present; no compilers, no wget, no curl.

### 4. Secret Management

No secrets are baked into the image.
Environment variables are the only injection point, and none are required by this app.

### 5. Dependency Scanning

- `pip-audit` scans dependencies on every PR.
- Trivy scans the built image for OS-level and Python CVEs.

### 6. SBOM Generation

A CycloneDX SBOM is generated in JSON format and stored as a workflow artifact.
It documents every direct and transitive dependency with version and license.

### 7. Artifact Signing (Cosign)

Keyless signing via Sigstore. The signing workflow is defined and ready;
it activates when an image is pushed to a registry.

See [signing.md](signing.md) for the full procedure.

### 8. Provenance

OCI labels (`org.opencontainers.image.*`) record the source repository, license,
and image title. GitHub Actions build provenance can be attached via SLSA provenance
actions (not yet implemented — see Improvements below).

## Trust Boundaries

| Boundary                  | Control                        |
|---------------------------|-------------------------------|
| Source code               | gitleaks + branch protection   |
| Dependencies              | pip-audit on every PR          |
| Build environment         | Pinned action versions         |
| Runtime image             | Trivy scan + non-root user     |
| Artifact authenticity     | Cosign keyless signing         |
| Transparency               | Rekor log                      |

## Known Limitations

- Trivy and Cosign run only in GitHub Actions (not installed locally).
- Cosign signing requires a pushed image with a registry digest.
- SLSA provenance (level 2+) is documented but not yet implemented.
- Base image (`python:3.12-slim`) may have OS-level CVEs at any given time;
  rebuild regularly and check Trivy reports.

## Improvement Paths

- Add SLSA provenance via `slsa-framework/slsa-github-generator`.
- Pin action versions to SHAs (not tags) for supply chain hardening.
- Switch to `gcr.io/distroless/python3` or a custom minimal base.
- Implement automated base image rebuild on upstream CVE alerts.
