#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

NAME="dl7-diff"

step "Vorbereitung: alten Container entfernen"
docker rm -f "$NAME" >/dev/null 2>&1 || true

step "Was zeigt docker diff?"
echo "- docker diff zeigt Änderungen im Dateisystem eines Containers."
echo "- Damit sieht man, welche Dateien seit dem Start verändert, erstellt oder gelöscht wurden."

step "Was zeigt docker history?"
echo "- docker history zeigt die Layer-Historie eines Docker-Images."
echo "- Damit kann man nachvollziehen, wie ein Image aufgebaut wurde."

step "nginx-Container starten"
cmd_preview docker run -d --name "$NAME" nginx:alpine
docker run -d --name "$NAME" nginx:alpine

echo
echo "Hinweis:"
echo "- Wir starten zuerst einen normalen Container."
echo "- Danach erzeugen wir absichtlich eine Änderung im Container-Dateisystem."

step "Laufende Container anzeigen"
cmd_preview docker ps
docker ps

step "Im Container eine Datei anlegen"
cmd_preview docker exec "$NAME" sh -c 'echo Hallo aus dem Container > /tmp/demo.txt'
docker exec "$NAME" sh -c 'echo Hallo aus dem Container > /tmp/demo.txt'

echo
echo "Erklärung:"
echo "- Wir schreiben eine neue Datei nach /tmp/demo.txt."
echo "- Diese Änderung gab es im ursprünglichen Image noch nicht."

step "Datei im Container anzeigen"
cmd_preview docker exec "$NAME" cat /tmp/demo.txt
docker exec "$NAME" cat /tmp/demo.txt

echo
echo "Was wollen wir hier sehen?"
echo "- Wir prüfen zuerst, ob die Datei wirklich im Container existiert."
echo "- Danach schauen wir mit docker diff, ob Docker diese Änderung erkennt."

step "Änderungen mit docker diff anzeigen"
cmd_preview docker diff "$NAME"
docker diff "$NAME"

echo
echo "Was wollen wir hier sehen?"
echo "- docker diff sollte zeigen, dass sich das Dateisystem des Containers verändert hat."
echo "- Typisch sind Markierungen für neue, geänderte oder gelöschte Dateien."

echo
echo "Hinweis zu den Markierungen:"
echo "- A = Added   → Datei oder Verzeichnis wurde neu erstellt"
echo "- C = Changed → bestehende Datei oder Verzeichnis wurde verändert"
echo "- D = Deleted → Datei oder Verzeichnis wurde gelöscht"

step "Gezielt nach /tmp suchen"
cmd_preview docker diff "$NAME" "|" grep /tmp
docker diff "$NAME" | grep /tmp || true

echo
echo "Erklärung:"
echo "- Mit grep filtern wir gezielt nach unserer Änderung."
echo "- So findet man in langen diff-Ausgaben schneller die relevante Stelle."

step "Image-History anzeigen"
cmd_preview docker history nginx:alpine
docker history nginx:alpine

echo
echo "Was wollen wir hier sehen?"
echo "- docker history zeigt die Layer des Images von oben nach unten."
echo "- So erkennt man, aus welchen Schritten das Image aufgebaut wurde."

echo
echo "Erklärung:"
echo "- Jeder Layer stammt aus einem Schritt beim Image-Bau."
echo "- Damit kann man besser verstehen, warum ein Image gross ist oder wie es entstanden ist."

step "Interpretation"
echo "- docker diff beantwortet die Frage: Was wurde im laufenden Container verändert?"
echo "- docker history beantwortet die Frage: Wie ist das Image grundsätzlich aufgebaut?"
echo "- Beides hilft beim Debuggen und Verstehen von Containern und Images."

step "Cleanup"
cmd_preview docker rm -f "$NAME"
docker rm -f "$NAME"

note "Fertig."