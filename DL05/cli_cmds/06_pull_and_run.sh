#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

DOCKERHUB_USER="${1:?Bitte Docker-Hub-User angeben}"
REMOTE_REPO="${2:-meinimage}"
REMOTE_TAG="${3:-1.0}"

cmd_preview docker pull "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
docker pull "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"

echo
cmd_preview docker images
docker images
echo
cmd_preview docker run --name "${REMOTE_REPO}_fromhub" "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
docker run --name "${REMOTE_REPO}_fromhub" "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
echo
cmd_preview docker ps -a
docker ps -a
