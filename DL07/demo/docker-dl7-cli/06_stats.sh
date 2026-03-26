#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NAME="dl7-stats"

step "Vorbereitung: alten Container entfernen"
docker rm -f "$NAME" >/dev/null 2>&1 || true

step "Was zeigt docker stats?"
echo "- docker stats zeigt die aktuelle Ressourcen-Nutzung eines laufenden Containers."
echo "- Typisch sind CPU, RAM, Netzwerkverkehr und je nach Umgebung weitere Werte wie Block I/O oder PIDs."

step "Warum ist das beim Debuggen nützlich?"
echo "- Damit erkennt man, ob ein Container zu viel CPU oder RAM verbraucht."
echo "- Das hilft bei Endlosschleifen, Speicherproblemen oder allgemein bei Performance-Problemen."

step "Container mit CPU-Last starten"
cmd_preview docker run -d --name "$NAME" alpine:3.20 sh -c 'while true; do :; done'
docker run -d --name "$NAME" alpine:3.20 sh -c 'while true; do :; done'

echo
echo "Hinweis:"
echo "- Dieser Container macht absichtlich sehr viel CPU-Last."
echo "- Die Endlosschleife dient nur dazu, in docker stats einen gut sichtbaren Effekt zu erzeugen."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

echo
echo "Wir warten kurz, damit sich die Last stabilisieren kann ..."
sleep 2

step "Stats einmalig anzeigen"
cmd_preview docker stats --no-stream "$NAME"
docker stats --no-stream "$NAME"

echo
echo "Was wollen wir hier sehen?"
echo "- Uns interessiert vor allem die CPU-Auslastung und der Speicherverbrauch."
echo "- Die CPU sollte wegen der Endlosschleife sichtbar belastet sein."

echo
echo "Erklärung zu typischen Spalten:"
echo "- CPU %: aktuelle Prozessor-Auslastung des Containers."
echo "- MEM USAGE / LIMIT: aktueller Speicherverbrauch im Verhältnis zum verfügbaren Limit."
echo "- NET I/O: empfangene und gesendete Netzwerkdaten."
echo "- BLOCK I/O: Lese- und Schreibzugriffe auf Datenträger."
echo "- PIDs: Anzahl Prozesse im Container."

step "Stats aller laufenden Container anzeigen"
cmd_preview docker stats --no-stream
docker stats --no-stream

echo
echo "Erklärung:"
echo "- Ohne Containernamen zeigt docker stats alle laufenden Container."
echo "- Das ist praktisch, wenn man schnell vergleichen möchte, welcher Container die meiste Last erzeugt."

step "Prozess im Container anschauen"
cmd_preview docker top "$NAME"
docker top "$NAME"

echo
echo "Zusammenhang:"
echo "- docker stats zeigt die Auswirkungen auf CPU und RAM."
echo "- docker top hilft danach zu prüfen, welcher Prozess diese Last verursacht."

step "Container stoppen"
cmd_preview docker rm -f "$NAME"
docker rm -f "$NAME"

echo
echo "Interpretation:"
echo "- docker stats beantwortet die Frage: Wie stark belastet der Container das System gerade?"
echo "- Wenn Werte auffällig hoch sind, schaut man oft als Nächstes mit docker top oder docker exec in den Container."

note "Fertig."