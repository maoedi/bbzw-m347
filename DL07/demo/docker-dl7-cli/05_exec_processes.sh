#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NAME="dl7-exec"

step "Vorbereitung: alten Container entfernen"
docker rm -f "$NAME" >/dev/null 2>&1 || true

step "Was macht docker exec?"
echo "- docker exec führt einen zusätzlichen Befehl in einem bereits laufenden Container aus."
echo "- Damit kann man von innen prüfen, ob Prozesse laufen, Dateien existieren oder ein Dienst erreichbar ist."

step "Warum schauen wir Prozesse an?"
echo "- Ein Container läuft im Normalfall so lange, wie sein Hauptprozess läuft."
echo "- Deshalb ist beim Debuggen oft wichtig: Welcher Prozess ist aktiv, und was ist PID 1?"

step "Container starten"
cmd_preview docker run -d --name "$NAME" ubuntu:22.04 sleep 60
docker run -d --name "$NAME" ubuntu:22.04 sleep 60

echo
echo "Hinweis:"
echo "- Der Container führt als Hauptprozess einfach 'sleep 60' aus."
echo "- Das ist Absicht, damit wir die Prozessliste gut beobachten können."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

step "Prozesse IM Container anzeigen"
cmd_preview docker exec "$NAME" sh -c 'ps -ef | head -n 20'
docker exec "$NAME" sh -c 'ps -ef | head -n 20'

echo
echo "Was wollen wir hier sehen?"
echo "- Wir möchten sehen, welche Prozesse im Container laufen."
echo "- Besonders wichtig ist der Hauptprozess, weil von ihm die Lebensdauer des Containers abhängt."

step "PID 1 im Container prüfen"
cmd_preview docker exec "$NAME" sh -c 'ps -p 1 -o pid,ppid,cmd'
docker exec "$NAME" sh -c 'ps -p 1 -o pid,ppid,cmd'

echo
echo "Was wollen wir hier sehen?"
echo "- PID 1 ist der Hauptprozess des Containers."
echo "- In diesem Beispiel sollte das der Befehl 'sleep 60' sein."

echo
echo "Bedeutung:"
echo "- Wenn PID 1 endet, stoppt normalerweise der ganze Container."
echo "- Viele Containerprobleme lassen sich darauf zurückführen, dass der falsche Prozess als PID 1 läuft oder sofort beendet wird."

step "Prozesse VON AUSSEN anzeigen"
cmd_preview docker top "$NAME"
docker top "$NAME"

echo
echo "Erklärung:"
echo "- docker top zeigt die laufenden Prozesse eines Containers von aussen an."
echo "- Das ist praktisch, wenn man schnell sehen will, was im Container läuft, ohne einen zusätzlichen Befehl im Container zu starten."

step "Zusätzlichen Befehl im Container ausführen"
cmd_preview docker exec "$NAME" sh -c 'echo Hallo aus dem Container'
docker exec "$NAME" sh -c 'echo Hallo aus dem Container'

echo
echo "Erklärung:"
echo "- docker exec ist nicht nur für Prozesslisten nützlich."
echo "- Man kann damit auch Tests, Dateiabfragen oder Netzwerkbefehle direkt im laufenden Container ausführen."

step "Container-Status prüfen"
cmd_preview docker ps -a
docker ps -a

echo
echo "Interpretation:"
echo "- docker exec beantwortet die Frage: Was sehe ich von innen?"
echo "- docker top beantwortet die Frage: Welche Prozesse laufen gerade?"
echo "- Beides zusammen hilft zu prüfen, ob der erwartete Hauptprozess wirklich aktiv ist."

step "Cleanup"
cmd_preview docker rm -f "$NAME"
docker rm -f "$NAME"

note "Fertig."