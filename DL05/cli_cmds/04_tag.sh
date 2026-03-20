#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

DOCKERHUB_USER="${1:?Bitte Docker-Hub-User angeben}"
LOCAL_IMAGE="${2:-meinimage}"
LOCAL_TAG="${3:-1.0}"
REMOTE_REPO="${4:-meinimage}"
REMOTE_TAG="${5:-1.0}"

cmd_preview docker tag "${LOCAL_IMAGE}:${LOCAL_TAG}" "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
docker tag "${LOCAL_IMAGE}:${LOCAL_TAG}" "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"

echo
echo "Quelle: ${LOCAL_IMAGE}:${LOCAL_TAG}"
echo "Ziel:   ${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
echo

cmd_preview docker images
docker images
