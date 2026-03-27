#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/cmd_preview.sh"

step "Docker CLI Übersicht (DL7 – Debugging & Beobachten)"

echo
echo "Diese Übersicht zeigt alle wichtigen Docker-Befehle,"
echo "die wir in dieser Doppellektion verwenden."
echo "Die Befehle werden hier NICHT ausgeführt."

hr

printf "%-25s %-35s %-50s\n" "Kategorie" "Befehl" "Wofür wird er verwendet?"
printf "%-25s %-35s %-50s\n" "-------------------------" "-----------------------------------" "--------------------------------------------------"

printf "%-25s %-35s %-50s\n" "System" "docker version" "Zeigt Version von Client und Server"
printf "%-25s %-35s %-50s\n" "System" "docker info" "Zeigt Informationen zum Docker-Daemon"

printf "%-25s %-35s %-50s\n" "Logs" "docker logs" "Zeigt stdout und stderr eines Containers"

printf "%-25s %-35s %-50s\n" "Analyse" "docker inspect" "Zeigt Konfiguration eines Containers (JSON)"

printf "%-25s %-35s %-50s\n" "Container intern" "docker exec" "Führt Befehle im laufenden Container aus"
printf "%-25s %-35s %-50s\n" "Prozesse" "docker top" "Zeigt laufende Prozesse im Container"

printf "%-25s %-35s %-50s\n" "Ressourcen" "docker stats" "Zeigt CPU, RAM und Netzwerkverbrauch"

printf "%-25s %-35s %-50s\n" "Netzwerk" "docker network create" "Erstellt ein eigenes Docker-Netzwerk"
printf "%-25s %-35s %-50s\n" "Netzwerk" "docker network inspect" "Zeigt Details eines Netzwerks"

printf "%-25s %-35s %-50s\n" "Events" "docker events" "Zeigt Live-Ereignisse von Docker"

printf "%-25s %-35s %-50s\n" "Dateisystem" "docker diff" "Zeigt Änderungen im Container-Dateisystem"

printf "%-25s %-35s %-50s\n" "Images" "docker history" "Zeigt Layer eines Docker-Images"

hr

echo
echo "Hinweis:"
echo "- Diese Befehle helfen dir beim systematischen Debuggen von Containern."
echo "- Ziel: Nicht raten, sondern beobachten und eingrenzen."

echo
echo "Typische Debug-Fragen:"
echo "1) Läuft der Container überhaupt?"
echo "2) Was sagen die Logs?"
echo "3) Stimmt die Konfiguration (inspect)?"
echo "4) Läuft der richtige Prozess?"
echo "5) Ist der Dienst intern erreichbar?"
echo "6) Stimmen Netzwerk und Ports?"

echo
note "Dieses Script dient nur als Übersicht und wird nicht interaktiv ausgeführt."