#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

LOCAL_IMAGE="${1:-meinimage}"
LOCAL_TAG="${2:-1.0}"
DOCKERHUB_USER="${3:-}"
REMOTE_REPO="${4:-meinimage}"
REMOTE_TAG="${5:-1.0}"

docker rm -f "${LOCAL_IMAGE}_test" 2>/dev/null || true
docker rm -f "${REMOTE_REPO}_fromhub" 2>/dev/null || true
docker rmi "${LOCAL_IMAGE}:${LOCAL_TAG}" 2>/dev/null || true

if [[ -n "$DOCKERHUB_USER" ]]; then
  docker rmi "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}" 2>/dev/null || true
fi

echo
docker images
echo
docker ps -a
