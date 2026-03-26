#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NET="dl7-net"
A="dl7-net-a"
B="dl7-net-b"

step "Vorbereitung: alte Container und altes Netzwerk entfernen"
docker rm -f "$A" "$B" >/dev/null 2>&1 || true
docker network rm "$NET" >/dev/null 2>&1 || true

step "Was ist ein Docker-Netzwerk?"
echo "- Ein Docker-Netzwerk verbindet Container miteinander."
echo "- In einem gemeinsamen Netzwerk können Container oft direkt über ihren Namen miteinander kommunizieren."

step "Warum ist das beim Debuggen wichtig?"
echo "- Viele Probleme entstehen nicht im Container selbst, sondern bei der Verbindung zwischen mehreren Containern."
echo "- Deshalb prüft man bei Netzwerkproblemen oft: Sind die Container im richtigen Netzwerk, und können sie sich gegenseitig erreichen?"

step "Eigenes Bridge-Netzwerk erstellen"
cmd_preview docker network create "$NET"
docker network create "$NET"

echo
echo "Erklärung:"
echo "- Wir erstellen absichtlich ein eigenes Netzwerk, damit die Struktur übersichtlich bleibt."
echo "- Das Netzwerk ist vom Typ Bridge, also ein privates Docker-Netzwerk auf diesem Host."

step "Ersten Container im Netzwerk starten"
cmd_preview docker run -d --name "$A" --network "$NET" alpine:3.20 sleep 60
docker run -d --name "$A" --network "$NET" alpine:3.20 sleep 60

step "Zweiten Container im Netzwerk starten"
cmd_preview docker run -d --name "$B" --network "$NET" alpine:3.20 sleep 60
docker run -d --name "$B" --network "$NET" alpine:3.20 sleep 60

echo
echo "Hinweis:"
echo "- Beide Container laufen jetzt im gleichen benutzerdefinierten Netzwerk."
echo "- Dadurch sollten sie sich gegenseitig per Namen finden können."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

step "Netzwerke anzeigen"
cmd_preview docker network ls
docker network ls

echo
echo "Erklärung:"
echo "- docker network ls zeigt alle vorhandenen Docker-Netzwerke."
echo "- So kann man prüfen, ob das gewünschte Netzwerk überhaupt existiert."

step "Netzwerk komplett inspizieren"
cmd_preview docker network inspect "$NET"
docker network inspect "$NET"

echo
echo "Was wollen wir hier sehen?"
echo "- Uns interessiert, welche Container im Netzwerk hängen."
echo "- Ausserdem sieht man hier oft IP-Adressen und weitere Netzwerkdetails."

step "Im Inspect-Output nach Containern suchen"
cmd_preview docker network inspect "$NET" "|" grep -A 20 '"Containers"'
docker network inspect "$NET" | grep -A 20 '"Containers"'

echo
echo "Bedeutung:"
echo "- Im Bereich \"Containers\" sieht man, welche Container mit diesem Netzwerk verbunden sind."
echo "- Dort findet man typischerweise auch Namen, IDs und interne IP-Adressen."

step "Namensauflösung und Erreichbarkeit testen"
cmd_preview docker exec "$A" ping -c 1 "$B"
docker exec "$A" ping -c 1 "$B"

echo
echo "Was wollen wir hier sehen?"
echo "- Container A versucht, Container B über dessen Namen zu erreichen."
echo "- Wenn das klappt, funktioniert das Docker-interne DNS im Netzwerk."

step "Optional: Netzwerkadresse im Container anschauen"
cmd_preview docker exec "$A" sh -c 'ip addr 2>/dev/null || ifconfig 2>/dev/null || true'
docker exec "$A" sh -c 'ip addr 2>/dev/null || ifconfig 2>/dev/null || true'

echo
echo "Erklärung:"
echo "- Damit kann man im Container nachsehen, welche Netzwerkschnittstellen vorhanden sind."
echo "- Je nach Image sind ip oder ifconfig allerdings nicht installiert."

step "Interpretation"
echo "- docker network create erstellt ein eigenes Netzwerk für mehrere Container."
echo "- docker network inspect zeigt, welche Container verbunden sind."
echo "- Der Ping-Test zeigt, ob sich Container im gleichen Netzwerk über ihren Namen erreichen können."

step "Cleanup: Container entfernen"
cmd_preview docker rm -f "$A" "$B"
docker rm -f "$A" "$B"

step "Cleanup: Netzwerk entfernen"
cmd_preview docker network rm "$NET"
docker network rm "$NET"

note "Fertig."