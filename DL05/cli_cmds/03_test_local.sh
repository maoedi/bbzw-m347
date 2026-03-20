#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

IMAGE_NAME="${1:-meinimage}"
IMAGE_TAG="${2:-1.0}"

cmd_preview docker run --name "${IMAGE_NAME}_test" "${IMAGE_NAME}:${IMAGE_TAG}"
docker run --name "${IMAGE_NAME}_test" "${IMAGE_NAME}:${IMAGE_TAG}" || true

echo
cmd_preview docker ps
docker ps
echo
cmd_preview docker ps -a
docker ps -a
