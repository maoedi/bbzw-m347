#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

TEMP_NAME="dl7-events-demo"

step "Vorbereitung: alten Demo-Container entfernen"
docker rm -f "$TEMP_NAME" >/dev/null 2>&1 || true

step "Was sind Docker-Events?"
echo "- Docker-Events sind Meldungen darüber, was Docker gerade tut, zum Beispiel create, start, stop oder destroy."
echo "- Damit kann man zeitlich beobachten, was mit Containern, Netzwerken oder anderen Docker-Objekten passiert."

step "Warum ist das beim Debuggen wichtig?"
echo "- Events helfen, Abläufe in der richtigen Reihenfolge zu verstehen."
echo "- Das ist besonders nützlich, wenn Container sofort wieder stoppen oder ständig neu gestartet werden."

step "Docker-Events live beobachten"
echo "Hinweis:"
echo "- Wir starten gleich im Hintergrund einen kurzlebigen Container."
echo "- Währenddessen läuft 'docker events' für einige Sekunden und zeigt die passenden Ereignisse an."

step "Aufbau des Befehls"
echo "Wir starten zwei Dinge gleichzeitig: docker events & ein kurzer Container"
echo "- sleep 1"
echo "  - wartet 1 Sekunde, damit 'docker events' sicher zuerst startet"
echo
echo "- docker run --name dl7-events-demo --rm debian:latest sleep 1"
echo "  - startet einen neuen Container"
echo "  - 'sleep 1' bedeutet: der Container läuft nur 1 Sekunde und beendet sich dann selbst"
echo
echo "- --rm"
echo "  - sorgt dafür, dass der Container nach dem Stop automatisch gelöscht wird"
echo
echo "- >/dev/null 2>&1"
echo "  - unterdrückt die normale Ausgabe des docker run Befehls"
echo
echo "- &"
echo "  - startet den docker run Befehl im Hintergrund"
echo
echo "- timeout 6 docker events"
echo "  - startet 'docker events' und zeigt Live-Ereignisse"
echo "  - nach 6 Sekunden wird der Befehl automatisch beendet"

cmd_preview bash -c "sleep 1; docker run --name $TEMP_NAME --rm debian:latest sleep 1 >/dev/null 2>&1 & timeout 6 docker events"
bash -c "sleep 1; docker run --name $TEMP_NAME --rm debian:latest sleep 1 >/dev/null 2>&1 & timeout 6 docker events"

echo
echo "Was wollten wir hier sehen?"
echo "- docker events zeigt Live-Ereignisse direkt während sie passieren."
echo "- Beim Start eines kurzlebigen Containers sieht man typischerweise create, start, die und destroy."

step "Typische Event-Namen einordnen"
echo "- create: Docker erstellt den Container."
echo "- start: Docker startet den Container."
echo "- die: Der Hauptprozess im Container ist beendet."
echo "- destroy: Der Container wird gelöscht."

echo
echo "Bedeutung:"
echo "- Die Reihenfolge der Events hilft zu verstehen, was wirklich passiert ist."
echo "- Gerade bei kurzlebigen oder fehlerhaften Containern sieht man hier oft mehr als nur in docker ps."

step "Prüfen, ob der Demo-Container schon wieder weg ist"
cmd_preview docker ps -a
docker ps -a

echo
echo "Erklärung:"
echo "- Weil wir den Container mit --rm gestartet haben, wird er nach dem Ende automatisch entfernt."
echo "- Das passt gut zur Event-Beobachtung, weil dabei auch das destroy-Event sichtbar wird."

step "Interpretation"
echo "- docker events beantwortet die Frage: Was ist wann passiert?"
echo "- Das ist besonders hilfreich, wenn man Start-, Stop- oder Restart-Probleme zeitlich nachvollziehen will."

note "Fertig."