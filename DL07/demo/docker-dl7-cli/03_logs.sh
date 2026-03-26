#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NAME="dl7-logs"
LOG_CMD="echo 'INFO: Start'; echo 'ERROR: Konfiguration fehlt!' 1>&2; echo 'INFO: Ich laufe...'; sleep 8"

step "Vorbereitung: alten Container entfernen"
docker rm -f "$NAME" >/dev/null 2>&1 || true

step "Was sind stdout und stderr?"
echo "- stdout (Standard Output): normale Ausgaben eines Programms (z.B. INFO-Meldungen)."
echo "- stderr (Standard Error): Ausgaben für Fehler und Warnungen."
echo "- Programme können selbst entscheiden, was sie wohin schreiben (z.B. Logs oder Errors)."
echo "- Docker sammelt beide Streams und zeigt sie gemeinsam mit 'docker logs' an."

step "Container starten, der stdout und stderr beschreibt"
cmd_preview docker run -d --name "$NAME" alpine:3.20 sh -c "$LOG_CMD"
docker run -d --name "$NAME" alpine:3.20 sh -c "$LOG_CMD"

echo
echo "Hinweis:"
echo "- Der Container läuft nur kurz (sleep 8 Sekunden) und stoppt dann automatisch."
echo "- Das ist Absicht: Wir wollen zeigen, dass docker logs auch bei gestoppten Containern funktioniert."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

echo
echo "Wir warten kurz, bis der Container beendet ist ..."
sleep 9

step "Alle Container anzeigen (inkl. gestoppte)"
cmd_preview docker ps -a
docker ps -a

echo
echo "Beobachtung:"
echo "- Der Container ist jetzt gestoppt."
echo "- Trotzdem existieren seine Logs weiterhin."

step "Logs komplett anzeigen"
cmd_preview docker logs "$NAME"
docker logs "$NAME"

echo
echo "Was wollen wir hier sehen?"
echo "- Wir wollen herausfinden, welche Meldungen der Container beim Start ausgegeben hat."
echo "- Besonders interessant sind ERROR-Zeilen."

echo
echo "Beobachtung:"
echo "- docker logs zeigt stdout und stderr zusammen an."
echo "- Deshalb sehen wir INFO- und ERROR-Meldungen gemischt."

step "Gezielt nach der ERROR-Zeile suchen"
cmd_preview docker logs "$NAME" "|" grep ERROR
docker logs "$NAME" | grep ERROR

echo
echo "Erklärung:"
echo "- Mit grep filtern wir nur die Fehlermeldungen heraus."
echo "- Das ist hilfreich bei grossen Logmengen."

step "Logs mit Zeitstempel anzeigen"
cmd_preview docker logs -t "$NAME"
docker logs -t "$NAME"

echo
echo "Erklärung:"
echo "- Mit -t sehen wir, wann jede Logzeile entstanden ist."
echo "- Das hilft beim zeitlichen Debugging."

step "Live-Logs beobachten (nur sinnvoll bei laufendem Container)"
echo "Hinweis: Der Container ist bereits gestoppt, daher kommen hier keine neuen Logs mehr."
cmd_preview timeout 3 docker logs -f "$NAME"
timeout 3 docker logs -f "$NAME" || true

echo
echo "Interpretation:"
echo "- Logs beantworten die Frage: Was hat der Container gemacht?"
echo "- Wichtig: Logs bleiben auch nach dem Stop erhalten."
echo "- docker logs funktioniert also auch für bereits beendete Container."

step "Cleanup"
cmd_preview docker rm -f "$NAME"
docker rm -f "$NAME"

note "Fertig."