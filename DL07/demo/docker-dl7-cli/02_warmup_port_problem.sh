#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

BROKEN_NAME="dl7-broken"
FIXED_NAME="dl7-fixed"
HOST_PORT="${1:-8088}"

step "Vorbereitung: alte Container entfernen"
docker rm -f "$BROKEN_NAME" "$FIXED_NAME" >/dev/null 2>&1 || true

step "Image bereitstellen"
cmd_preview docker pull nginx:alpine
docker pull nginx:alpine

step "Problemfall: nginx OHNE Port-Mapping starten"
cmd_preview docker run -d --name "$BROKEN_NAME" nginx:alpine
docker run -d --name "$BROKEN_NAME" nginx:alpine

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

note "Der Container läuft, aber wir haben noch keinen Port auf den Host veröffentlicht."

step "Test auf dem Host: Ist localhost:$HOST_PORT erreichbar?"
echo "curl http://127.0.0.1:$HOST_PORT"
if curl -I --max-time 2 "http://127.0.0.1:$HOST_PORT" 2>/dev/null; then
    echo "Unerwartet: erreichbar"
else
    echo "Wie erwartet: NICHT erreichbar"
fi

step "Inspect komplett"
cmd_preview docker inspect "$BROKEN_NAME"
docker inspect "$BROKEN_NAME"

echo
echo "Erklärung:"
echo "- docker inspect zeigt die komplette Container-Konfiguration als JSON."
echo "- Das ist oft zu viel auf einmal, deshalb filtern wir im nächsten Schritt gezielt nach Ports."

step "Inspect Ports gezielt filtern"
cmd_preview docker inspect "$BROKEN_NAME" '|' grep -A 5 '"Ports"'
docker inspect "$BROKEN_NAME" | grep -A 5 '"Ports"'

echo
echo "Was wollen wir hier sehen?"
echo "- Uns interessiert, ob Container-Port 80/tcp auf einen Host-Port veröffentlicht wurde."
echo "- Die relevante Stelle ist der Bereich \"Ports\" im inspect-Output."

echo
echo "Bedeutung von {\"80/tcp\":null}:"
echo "- 80/tcp existiert im Container."
echo "- null bedeutet: Es gibt KEIN Mapping auf einen Host-Port."
echo "- Genau deshalb ist nginx im Container erreichbar, aber nicht über localhost auf dem Host."

step "Test im Container: HTML-Seite direkt aus nginx holen"
cmd_preview docker exec "$BROKEN_NAME" sh -c 'wget -qO- http://127.0.0.1 | head -n 12'
docker exec "$BROKEN_NAME" sh -c 'wget -qO- http://127.0.0.1 | head -n 12'

echo
echo "Erklärung:"
echo "- Hier testen wir den Webserver direkt IM Container über 127.0.0.1."
echo "- Wenn HTML erscheint, läuft nginx intern korrekt."

step "Optional: HTTP-Statuszeile im Container anzeigen"
cmd_preview docker exec "$BROKEN_NAME" sh -c 'wget -S -O- http://127.0.0.1 2>&1 | head -n 5'
docker exec "$BROKEN_NAME" sh -c 'wget -S -O- http://127.0.0.1 2>&1 | head -n 5'

echo
echo "Interpretation:"
echo "- Im Container funktioniert der Dienst."
echo "- Vom Host aus funktioniert es nicht."
echo "- Die Ursache ist also nicht nginx selbst, sondern das fehlende Port-Mapping."

step "Fix: Container neu starten MIT Port-Mapping"
cmd_preview docker rm -f "$BROKEN_NAME"
docker rm -f "$BROKEN_NAME"

cmd_preview docker run -d --name "$FIXED_NAME" -p "$HOST_PORT:80" nginx:alpine
docker run -d --name "$FIXED_NAME" -p "$HOST_PORT:80" nginx:alpine

step "Inspect nach dem Fix"
cmd_preview docker inspect "$FIXED_NAME" '|' grep -A 8 '"Ports"'
docker inspect "$FIXED_NAME" | grep -A 8 '"Ports"'

echo
echo "Jetzt sollte bei 80/tcp ein HostPort sichtbar sein."
echo "Das ist der entscheidende Unterschied zum kaputten Beispiel."

step "Test vom Host nach dem Fix"
cmd_preview curl -I "http://127.0.0.1:$HOST_PORT"
curl -I "http://127.0.0.1:$HOST_PORT"

echo
echo "Diagnose:"
echo "- Vorher: {\"80/tcp\":null}  -> kein Host-Port veröffentlicht"
echo "- Nachher: HostPort vorhanden -> Dienst vom Host erreichbar"

step "Cleanup"
cmd_preview docker rm -f "$FIXED_NAME"
docker rm -f "$FIXED_NAME"