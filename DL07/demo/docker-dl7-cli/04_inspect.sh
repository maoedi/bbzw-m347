#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NAME="dl7-inspect"
HOST_PORT="${1:-8089}"

step "Vorbereitung: alten Container entfernen"
docker rm -f "$NAME" >/dev/null 2>&1 || true

step "Was macht docker inspect?"
echo "- docker inspect zeigt die komplette Konfiguration und den aktuellen Zustand eines Docker-Objekts als JSON."
echo "- Damit kann man sehr gezielt nachsehen, wie ein Container gestartet wurde und welche Einstellungen wirklich aktiv sind."

step "Container mit ENV-Variablen und Port-Mapping starten"
cmd_preview docker run -d --name "$NAME" -e APP_MODE=demo -e APP_PORT=80 -p "$HOST_PORT:80" nginx:alpine
docker run -d --name "$NAME" -e APP_MODE=demo -e APP_PORT=80 -p "$HOST_PORT:80" nginx:alpine

echo
echo "Hinweis:"
echo "- Wir setzen absichtlich zwei ENV-Variablen."
echo "- Ausserdem veröffentlichen wir Container-Port 80 auf den Host-Port $HOST_PORT."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

step "Inspect komplett"
cmd_preview docker inspect "$NAME"
docker inspect "$NAME"

echo
echo "Erklärung:"
echo "- Der volle inspect-Output ist sehr umfangreich."
echo "- Deshalb filtern wir im nächsten Schritt gezielt die Stellen, die wir wirklich analysieren wollen."

step "ENV-Bereich im inspect-Output suchen"
cmd_preview docker inspect "$NAME" "|" grep -A 10 '"Env"'
docker inspect "$NAME" | grep -A 10 '"Env"'

echo
echo "Was wollen wir hier sehen?"
echo "- Uns interessiert, welche Umgebungsvariablen im Container gesetzt wurden."
echo "- Besonders wichtig sind hier APP_MODE=demo und APP_PORT=80."

echo
echo "Bedeutung:"
echo "- Der Bereich \"Env\" zeigt die Umgebungsvariablen, die beim Start an den Container übergeben wurden."
echo "- So kann man prüfen, ob eine Anwendung wirklich mit den erwarteten Einstellungen gestartet wurde."

step "Ports-Bereich im inspect-Output suchen"
cmd_preview docker inspect "$NAME" "|" grep -A 8 '"Ports"'
docker inspect "$NAME" | grep -A 8 '"Ports"'

echo
echo "Was wollen wir hier sehen?"
echo "- Uns interessiert, ob Container-Port 80/tcp auf einen Host-Port gemappt wurde."
echo "- Hier sollte sichtbar sein, dass 80/tcp auf Host-Port $HOST_PORT veröffentlicht ist."

echo
echo "Bedeutung:"
echo "- Wenn bei 80/tcp ein HostPort eingetragen ist, kann der Dienst vom Host aus erreicht werden."
echo "- Fehlt dieser Eintrag oder steht dort null, wurde kein Port veröffentlicht."

step "Cmd-Bereich im inspect-Output suchen"
cmd_preview docker inspect "$NAME" "|" grep -A 5 '"Cmd"'
docker inspect "$NAME" | grep -A 5 '"Cmd"'

echo
echo "Was wollen wir hier sehen?"
echo "- Der Bereich \"Cmd\" zeigt, welcher Startbefehl im Container ausgeführt wird."
echo "- Das ist wichtig, wenn ein Container zwar startet, aber nicht das tut, was man erwartet."

step "HTTP-Test vom Host"
cmd_preview curl -I "http://127.0.0.1:$HOST_PORT"
curl -I "http://127.0.0.1:$HOST_PORT"

echo
echo "Interpretation:"
echo "- inspect beantwortet die Frage: Wie wurde der Container wirklich gestartet?"
echo "- Besonders wichtig beim Debuggen sind Cmd, Env, Ports, Volumes und Health."

step "Optional: ENV direkt im Container prüfen"
cmd_preview docker exec "$NAME" sh -c 'env | grep "^APP_"'
docker exec "$NAME" sh -c 'env | grep "^APP_"'

echo
echo "Erklärung:"
echo "- Mit inspect sehen wir die Konfiguration von aussen."
echo "- Mit docker exec können wir zusätzlich im Container prüfen, ob die Variablen tatsächlich vorhanden sind."

step "Cleanup"
cmd_preview docker rm -f "$NAME"
docker rm -f "$NAME"

note "Fertig."