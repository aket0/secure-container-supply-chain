# Artifact Signing with Cosign

## Overview

This project uses [Sigstore Cosign](https://docs.sigstore.dev/cosign/overview/) for
keyless artifact signing. Signing happens in GitHub Actions using the OIDC token issued
by GitHub, so no long-lived private key is stored anywhere.

## Chain of Trust

```
GitHub OIDC token
       ↓
  Fulcio CA (Sigstore)   ←  issues short-lived certificate bound to the workflow identity
       ↓
  Cosign signs image digest
       ↓
  Rekor transparency log  ←  records the signature publicly
       ↓
  Verifier: cosign verify  ←  checks certificate + log entry
```

## Prerequisites (for manual or external registry signing)

- A container registry (Docker Hub, GHCR, ECR, …)
- `cosign` installed (`cosign-installer` GitHub Action or `brew install cosign`)
- The image pushed to the registry

## Signing a Pushed Image

```bash
# After building and pushing the image
IMAGE="ghcr.io/aket0/secure-supply-chain-app"
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $IMAGE)

# Keyless sign (requires browser auth or GitHub Actions OIDC)
cosign sign --yes "$DIGEST"
```

## Verifying a Signature

```bash
# Verify keyless signature — checks Rekor and the certificate chain
cosign verify \
  --certificate-identity "https://github.com/aket0/secure-container-supply-chain/.github/workflows/supply-chain.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  "$IMAGE@$DIGEST"
```

## What is NOT signed locally

- Local builds (no registry, no digest reference available)
- PR builds (not pushed, no signing)

## Limitations

- Keyless signing requires GitHub Actions OIDC. It cannot run offline or in an
  environment without OIDC token support.
- The signing workflow is defined in `supply-chain.yml` but the `cosign sign` step
  requires a pushed image with a registry digest. It is documented here and ready to
  activate once a registry is configured.
