#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Corvus Air-Gap Packaging Script
# Builds a Docker image and packages everything needed for
# deployment in an air-gapped GovCloud environment.
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="corvus-govcloud"
IMAGE_TAG="latest"
TRANSFER_DIR="${REPO_ROOT}/transfer-package"

echo "=== Corvus Air-Gap Packaging ==="
echo "Repository: ${REPO_ROOT}"
echo ""

# Clean previous transfer package
rm -rf "${TRANSFER_DIR}"
mkdir -p "${TRANSFER_DIR}"

# Step 1: Build Docker image
echo "[1/5] Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" "${REPO_ROOT}"
echo "  Image built: ${IMAGE_NAME}:${IMAGE_TAG}"

# Step 2: Save image as tarball
echo "[2/5] Exporting Docker image..."
docker save "${IMAGE_NAME}:${IMAGE_TAG}" | gzip > "${TRANSFER_DIR}/${IMAGE_NAME}.tar.gz"
IMAGE_SIZE=$(du -h "${TRANSFER_DIR}/${IMAGE_NAME}.tar.gz" | cut -f1)
echo "  Image saved: ${IMAGE_SIZE}"

# Step 3: Copy deployment files
echo "[3/5] Copying deployment files..."
cp "${REPO_ROOT}/.env.govcloud.example" "${TRANSFER_DIR}/env.govcloud.example"
cp "${REPO_ROOT}/docker-compose.yml" "${TRANSFER_DIR}/"
cp "${REPO_ROOT}/docker-compose.govcloud.yml" "${TRANSFER_DIR}/"
if [ -f "${REPO_ROOT}/docs/GOVCLOUD_DEPLOY.md" ]; then
    cp "${REPO_ROOT}/docs/GOVCLOUD_DEPLOY.md" "${TRANSFER_DIR}/"
fi

# Step 4: Generate SHA256 manifest (CMMC integrity verification)
echo "[4/5] Generating SHA256 manifest..."
cd "${TRANSFER_DIR}"
sha256sum * > SHA256SUMS
cd "${REPO_ROOT}"
echo "  Manifest: SHA256SUMS"

# Step 5: Report
echo "[5/5] Package complete."
echo ""
echo "=== Transfer Package Contents ==="
ls -lh "${TRANSFER_DIR}/"
echo ""
TOTAL_SIZE=$(du -sh "${TRANSFER_DIR}" | cut -f1)
echo "Total package size: ${TOTAL_SIZE}"
echo "Location: ${TRANSFER_DIR}/"
echo ""
echo "=== Transfer Instructions ==="
echo "1. Copy ${TRANSFER_DIR}/ to approved transfer media"
echo "2. On GovCloud host: docker load < corvus-govcloud.tar.gz"
echo "3. Copy env.govcloud.example to .env and configure"
echo "4. docker compose -f docker-compose.yml -f docker-compose.govcloud.yml up"
echo "5. Verify: curl http://localhost:8002/admin/health-check"
