#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

DEMO_CONTAINER="dl7-demo"
DEMO_NET="dl7-demo-net"

step "Vorbereitung: Demo-Container und Netzwerk aufräumen"
docker rm -f "$DEMO_CONTAINER" >/dev/null 2>&1 || true
docker network rm "$DEMO_NET" >/dev/null 2>&1 || true

step "Demo-Container starten (für mehrere Befehle notwendig)"
cmd_preview docker run -d --name "$DEMO_CONTAINER" nginx:alpine
docker run -d --name "$DEMO_CONTAINER" nginx:alpine

# --------------------------------------------------
# version
# --------------------------------------------------
step "docker version (client.version())"
cmd_preview docker version
docker version

note "Zeigt die Version von Docker Client und Server."
echo "Nützlich um zu prüfen, ob Client und Daemon kompatibel sind."

# --------------------------------------------------
# info
# --------------------------------------------------
step "docker info (client.info())"
cmd_preview docker info
docker info

note "Zeigt Systeminformationen des Docker-Daemons."
echo "Hilfreich für Debugging von Umgebung, Storage und Anzahl Container/Images."

# --------------------------------------------------
# logs
# --------------------------------------------------
step "docker logs (container.logs())"
cmd_preview docker logs "$DEMO_CONTAINER"
docker logs "$DEMO_CONTAINER"

note "Zeigt stdout und stderr eines Containers."
echo "Wichtigster Einstiegspunkt, um Fehler im Container zu erkennen."

# --------------------------------------------------
# inspect
# --------------------------------------------------
step "docker inspect (container.attrs)"
cmd_preview docker inspect "$DEMO_CONTAINER"
docker inspect "$DEMO_CONTAINER" --format 'Name={{.Name}} Ports={{json .NetworkSettings.Ports}}'

note "Zeigt die komplette Konfiguration eines Containers als JSON."
echo "Wird verwendet, um Details wie Ports, ENV oder Startbefehl zu analysieren."

# --------------------------------------------------
# exec
# --------------------------------------------------
step "docker exec (container.exec_run())"
cmd_preview docker exec "$DEMO_CONTAINER" sh -c 'echo Hallo aus dem Container'
docker exec "$DEMO_CONTAINER" sh -c 'echo Hallo aus dem Container'

note "Führt einen Befehl in einem laufenden Container aus."
echo "Nützlich, um von innen zu testen oder Debugging durchzuführen."

# --------------------------------------------------
# top
# --------------------------------------------------
step "docker top (container.top())"
cmd_preview docker top "$DEMO_CONTAINER"
docker top "$DEMO_CONTAINER"

note "Zeigt laufende Prozesse im Container."
echo "Hilft zu prüfen, ob der erwartete Prozess wirklich läuft."

# --------------------------------------------------
# stats
# --------------------------------------------------
step "docker stats (container.stats())"
cmd_preview docker stats --no-stream "$DEMO_CONTAINER"
docker stats --no-stream "$DEMO_CONTAINER"

note "Zeigt CPU-, RAM- und Netzwerkverbrauch eines Containers."
echo "Wichtig bei Performance-Problemen oder hoher Last."

# --------------------------------------------------
# network create
# --------------------------------------------------
step "docker network create (client.networks.create())"
cmd_preview docker network create "$DEMO_NET"
docker network create "$DEMO_NET"

note "Erstellt ein eigenes Docker-Netzwerk."
echo "Container können sich darin gegenseitig per Namen erreichen."

# --------------------------------------------------
# events
# --------------------------------------------------
step "docker events (client.events())"
echo "Hinweis: Läuft 5 Sekunden..."
cmd_preview timeout 5 docker events
timeout 5 docker events || true

note "Zeigt Live-Events von Docker (z.B. start, stop, destroy)."
echo "Hilfreich, um zeitliche Abläufe und Fehler zu verstehen."

# --------------------------------------------------
# diff
# --------------------------------------------------
step "docker diff (container.diff())"
cmd_preview docker exec "$DEMO_CONTAINER" sh -c 'echo test > /tmp/test.txt'
docker exec "$DEMO_CONTAINER" sh -c 'echo test > /tmp/test.txt'

cmd_preview docker diff "$DEMO_CONTAINER"
docker diff "$DEMO_CONTAINER"

note "Zeigt Änderungen im Dateisystem eines Containers."
echo "Hilfreich um zu sehen, was eine Anwendung im Container verändert."

# --------------------------------------------------
# history
# --------------------------------------------------
step "docker history (image.history())"
cmd_preview docker history nginx:alpine
docker history nginx:alpine

note "Zeigt die Layer-Historie eines Images."
echo "Hilfreich um zu verstehen, wie ein Image aufgebaut ist."

# --------------------------------------------------
# Cleanup
# --------------------------------------------------
step "Cleanup"
cmd_preview docker rm -f "$DEMO_CONTAINER"
docker rm -f "$DEMO_CONTAINER"

cmd_preview docker network rm "$DEMO_NET"
docker network rm "$DEMO_NET"

note "Fertig."