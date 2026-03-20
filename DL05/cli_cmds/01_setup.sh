#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-docker-uebung}"

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

cat > Dockerfile <<'EOF'
FROM ubuntu:22.04
CMD ["echo", "Hallo aus meinem Docker Container"]
EOF

echo "Projektordner erstellt: $PROJECT_DIR"
echo "Dockerfile wurde angelegt."
echo
cat Dockerfile
