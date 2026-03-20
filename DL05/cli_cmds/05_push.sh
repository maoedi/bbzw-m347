#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

DOCKERHUB_USER="${1:?Bitte Docker-Hub-User angeben}"
REMOTE_REPO="${2:-meinimage}"
REMOTE_TAG="${3:-1.0}"

cmd_preview docker login
docker login
cmd_preview docker push "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
docker push "${DOCKERHUB_USER}/${REMOTE_REPO}:${REMOTE_TAG}"
