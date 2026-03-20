#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

PROJECT_DIR="${1:-docker-uebung}"
IMAGE_NAME="${2:-meinimage}"
IMAGE_TAG="${3:-1.0}"

cd "$PROJECT_DIR"
cmd_preview docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" 
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo
cmd_preview docker images
docker images

