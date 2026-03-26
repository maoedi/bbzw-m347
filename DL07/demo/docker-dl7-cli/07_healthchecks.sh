#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

OK_NAME="dl7-hc-ok"
BAD_NAME="dl7-hc-bad"

step "Vorbereitung: alte Container entfernen"
docker rm -f "$OK_NAME" "$BAD_NAME" >/dev/null 2>&1 || true

step "Was ist ein Healthcheck?"
echo "- Ein Healthcheck ist ein Test, den Docker regelmässig im Container ausführt."
echo "- Damit kann Docker prüfen, ob ein Dienst im Container wirklich funktioniert und nicht nur läuft."

step "Warum ist das beim Debuggen wichtig?"
echo "- Ein Container kann den Status running haben und trotzdem kaputt sein."
echo "- Healthchecks unterscheiden deshalb zwischen 'läuft' und 'ist tatsächlich gesund'."

step "Container mit funktionierendem Healthcheck starten"
cmd_preview docker run -d --name "$OK_NAME" --health-cmd="wget -qO- http://127.0.0.1 >/dev/null || exit 1" --health-interval=2s --health-timeout=1s --health-retries=3 nginx:alpine
docker run -d --name "$OK_NAME" \
  --health-cmd="wget -qO- http://127.0.0.1 >/dev/null || exit 1" \
  --health-interval=2s \
  --health-timeout=1s \
  --health-retries=3 \
  nginx:alpine

echo
echo "Erklärung:"
echo "- Dieser Healthcheck ruft im Container die lokale nginx-Seite auf."
echo "- Wenn der Aufruf funktioniert, bleibt der Container healthy."

step "Container mit absichtlich falschem Healthcheck starten"
cmd_preview docker run -d --name "$BAD_NAME" --health-cmd="wget -qO- http://127.0.0.1:9999 >/dev/null || exit 1" --health-interval=2s --health-timeout=1s --health-retries=2 nginx:alpine
docker run -d --name "$BAD_NAME" \
  --health-cmd="wget -qO- http://127.0.0.1:9999 >/dev/null || exit 1" \
  --health-interval=2s \
  --health-timeout=1s \
  --health-retries=2 \
  nginx:alpine

echo
echo "Erklärung:"
echo "- Hier testet Docker absichtlich den falschen Port 9999."
echo "- Der Container läuft zwar, aber der Healthcheck muss fehlschlagen."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

step "Health-Status beobachten"
echo "Wir beobachten jetzt einige Sekunden lang, wie sich der Status entwickelt."
for i in {1..8}; do
    echo
    echo "t=${i}s"
    docker inspect --format 'ok={{.State.Health.Status}} bad={{.State.Health.Status}}' "$OK_NAME" "$BAD_NAME"
    sleep 1
done

echo
echo "Was wollen wir hier sehen?"
echo "- Beide Container starten zuerst meist mit dem Status starting."
echo "- Danach sollte der erste Container healthy und der zweite unhealthy werden."

step "Health-Bereich des gesunden Containers anzeigen"
cmd_preview docker inspect "$OK_NAME" "|" grep -A 20 '"Health"'
docker inspect "$OK_NAME" | grep -A 20 '"Health"'

echo
echo "Erklärung:"
echo "- Im Bereich \"Health\" sieht man den aktuellen Status und oft auch frühere Prüfungen."
echo "- So erkennt man, ob der Test erfolgreich war und wie Docker entschieden hat."

step "Health-Bereich des ungesunden Containers anzeigen"
cmd_preview docker inspect "$BAD_NAME" "|" grep -A 20 '"Health"'
docker inspect "$BAD_NAME" | grep -A 20 '"Health"'

echo
echo "Was sehen wir hier?"
echo "- Beim ungesunden Container sollte der Status unhealthy sein."
echo "- Zusätzlich sind oft Fehlermeldungen oder Exit-Codes der letzten Prüfungen sichtbar."

step "Containerliste mit Health-Status anzeigen"
cmd_preview docker ps
docker ps

echo
echo "Interpretation:"
echo "- docker ps zeigt, dass ein Container laufen kann, obwohl sein Healthcheck fehlgeschlagen ist."
echo "- Genau deshalb ist ein Healthcheck nützlich: running bedeutet nicht automatisch healthy."

step "Cleanup"
cmd_preview docker rm -f "$OK_NAME" "$BAD_NAME"
docker rm -f "$OK_NAME" "$BAD_NAME"

note "Fertig."