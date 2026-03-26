#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

step "Docker Version prüfen"
cmd_preview docker version
docker version

step "Docker Systeminfo anzeigen"
cmd_preview docker info
docker info

note "Wenn hier Fehler auftreten: Docker läuft nicht oder keine Berechtigung"
