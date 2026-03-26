#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Markus Ineichen
Markus Ineichen, CC BY 4.0

DL6 – Docker-Container

Dieses Skript zeigt die wichtigsten Punkte für Docker-Container verwenden:
- Container-Lebenszeit (create/start/stop/rm)  → "run ist create + start"
- Ports veröffentlichen (publish)
- ENV (Umgebungsvariablen) übergeben
- Volumes: Bind-Mount vs. Named Volume (Persistenz verstehen)
- Cleanup: Ressourcen bewusst aufräumen

WICHTIG: Wir steuern Docker nur über Python (docker SDK), NICHT über die CLI.

Voraussetzungen (einmalig):
1) Docker läuft (Docker Desktop oder Docker Engine)
2) Python 3.10+ (geht auch meist früher)
3) Docker SDK installieren:
   pip install docker

Start:
   python dl6_container_runtime.py

Optional:
   python dl6_container_runtime.py --no-pause     (ohne ENTER-Pausen)
   python dl6_container_runtime.py --step volumes (nur einen Schritt, hier volumes)
   weitere Schritte: intro, lifecycle, ports, db, cleanup

SICHERHEIT:
- Das Skript erstellt Container/Volumes mit Label "dl6=true".
- Cleanup löscht nur Ressourcen, die dieses Skript erstellt (Label oder Name).
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import textwrap
import time
from pathlib import Path
from typing import Iterable, Optional

import docker
from docker.errors import APIError, NotFound
from docker.types import Mount


# ----------------------------
# Einstellungen (leicht ändern)
# ----------------------------

LAB_LABEL = {"dl6": "true", "lesson": "dl6"}

# Ich benutze bewusst Namen mit Prefix, damit alles gut erkennbar ist.
NAME_UBUNTU = "dl6_basics_container"
NAME_NGINX = "dl6_nginx_web"
NAME_REDIS_NO_VOL = "dl6_redis_no_volume"
NAME_REDIS_WITH_VOL = "dl6_redis_with_volume"

VOL_NAMED_DEMO = "dl6_named_volume_demo"
VOL_REDIS = "dl6_redis_data"

# Images (klein und schnell, aber bekannt)
IMG_ALPINE = "alpine:3.20"
IMG_NGINX = "nginx:1.27-alpine"
IMG_REDIS = "redis:7.4-alpine"


# ----------------------------
# Hilfsfunktionen
# ----------------------------

def hr() -> None:
    print("\n" + "-" * 78 + "\n")


def title(t: str) -> None:
    hr()
    print(t)
    hr()


def pause(no_pause: bool, msg: str = "Drücke ENTER, um weiterzumachen …") -> None:
    if no_pause:
        return
    try:
        input(msg)
    except KeyboardInterrupt:
        print("\nAbbruch durch Nutzer.")
        sys.exit(1)


def explain(text: str) -> None:
    print(textwrap.fill(text, width=78))


def pick_free_port(preferred: int) -> int:
    """Nimmt preferred, wenn frei. Sonst sucht einen freien Port."""
    if is_port_free(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def is_port_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def decode_output(output: object) -> str:
    if output is None:
        return ""
    if isinstance(output, (bytes, bytearray)):
        return output.decode("utf-8", errors="replace")
    return str(output)


def docker_client() -> docker.DockerClient:
    """Verbindet sich mit Docker (läuft Docker nicht → klare Fehlermeldung)."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        print("❌ Ich kann Docker nicht erreichen.")
        print("   Prüfe bitte: Läuft Docker Desktop / Docker Engine?")
        print("   Technisches Detail:", repr(e))
        sys.exit(2)


def ensure_image(client: docker.DockerClient, image: str) -> None:
    """Image ziehen, falls es lokal noch nicht vorhanden ist."""
    print(f"📦 Stelle sicher, dass das Image da ist: {image}")
    try:
        client.images.pull(image)
        print("   ✅ ok")
    except APIError as e:
        print("   ❌ Image konnte nicht geladen werden:", e)
        sys.exit(3)


def safe_remove_container(client: docker.DockerClient, name: str) -> None:
    """Container entfernen, wenn vorhanden (auch wenn er läuft)."""
    try:
        c = client.containers.get(name)
    except NotFound:
        return
    try:
        if c.status == "running":
            print(f"🛑 Stoppe alten Container {name} …")
            c.stop(timeout=10)
        print(f"🧹 Entferne alten Container {name} …")
        c.remove(force=True)
    except APIError as e:
        print(f"⚠️  Konnte Container {name} nicht entfernen:", e)


def safe_remove_volume(client: docker.DockerClient, name: str) -> None:
    try:
        v = client.volumes.get(name)
    except NotFound:
        return
    try:
        print(f"🧹 Entferne Volume {name} …")
        v.remove(force=True)
    except APIError as e:
        print(f"⚠️  Konnte Volume {name} nicht entfernen:", e)


def sh(container, cmd: str) -> tuple[int, str]:
    """Führt einen Befehl im Container aus (wie 'docker exec')."""
    res = container.exec_run(cmd)
    return int(res.exit_code), decode_output(res.output).strip()


def wait_until_running(container, timeout_s: int = 20) -> None:
    """Wartet, bis Container wirklich läuft."""
    start = time.time()
    while time.time() - start < timeout_s:
        container.reload()
        if container.status == "running":
            return
        time.sleep(0.3)
    raise TimeoutError("Container wurde nicht 'running' innerhalb des Timeouts.")


def list_lab_resources(client: docker.DockerClient) -> None:
    """Zeigt, was das Skript angelegt hat (Container + Volumes)."""
    print("📋 Aktuelle Lab-Ressourcen (Label dl6=true):")
    containers = client.containers.list(all=True, filters={"label": "dl6=true"})
    volumes = client.volumes.list(filters={"label": "dl6=true"})

    if not containers:
        print("  - keine Container")
    else:
        for c in containers:
            c.reload()
            print(f"  - Container: {c.name:24} | status={c.status}")

    if not volumes:
        print("  - keine Volumes")
    else:
        for v in volumes:
            print(f"  - Volume:   {v.name}")


# ----------------------------
# Schritt 0–15: Einstieg
# ----------------------------

def step_intro(no_pause: bool) -> None:
    title("0–15: Einstieg – Was passiert beim Löschen des Containers?")
    explain(
        "Stell dir vor, du hast einen Container, der Daten schreibt (z.B. eine Datenbank). "
        "Was passiert, wenn du den Container löschst? Sind die Daten weg – oder bleiben sie?"
    )
    pause(no_pause, "👉 Schreibe deine Vermutung in deinen Kopf 🙂 und drücke ENTER …")


# ----------------------------
# Schritt 15–30: Input (kurz)
# ----------------------------

def step_input(no_pause: bool) -> None:
    title("15–30: Input – Lebenszeit, Ports, ENV, Volumes (kurz & einfach)")
    explain(
        "Ein Container ist wie ein laufender Prozess, nur 'eingepackt'. "
        "Wichtig: 'run' ist im Prinzip 'create + start'. "
        "Stoppen beendet den Prozess – der Container kann aber noch existieren. "
        "Erst 'rm' löscht den Container (seine eigene Schreib-Schicht)."
    )
    print()
    explain(
        "Ports: Programme im Container hören auf einem Container-Port (z.B. 80 oder 6379). "
        "Damit du von deinem PC aus drauf zugreifen kannst, musst du einen Host-Port "
        "auf den Container-Port abbilden (publish)."
    )
    print()
    explain(
        "ENV: Umgebungsvariablen sind einfache Schlüssel/Wert-Paare, die du beim Start "
        "mitgeben kannst (z.B. PASSWORT=...). Sie stehen dann im Container zur Verfügung."
    )
    print()
    explain(
        "Volumes: Damit Daten länger leben als ein Container, nutzt man Volumes. "
        "Zwei wichtige Arten: "
        "1) Bind-Mount = Ordner vom Host in den Container einhängen (du siehst die Dateien direkt). "
        "2) Named Volume = Docker verwaltet den Speicherbereich (gut für Persistenz)."
    )
    pause(no_pause)


# ----------------------------
# Schritt: Container create/start/stop/rm + Labels
# ----------------------------

def step_container_lifecycle(client: docker.DockerClient, no_pause: bool) -> None:
    title("Demo 1: Container-Lebenszeit (create/start/stop/rm) + Labels")
    ensure_image(client, IMG_ALPINE)
    safe_remove_container(client, NAME_UBUNTU)

    explain(
        "Wir erstellen einen Container (create). Er ist dann 'da', aber läuft noch nicht. "
        "Dann starten wir ihn (start), stoppen ihn (stop) und löschen ihn (rm)."
    )

    pause(no_pause)

    # Container erzeugen (läuft noch nicht)
    container = client.containers.create(
        IMG_ALPINE,
        name=NAME_UBUNTU,
        command=["sh", "-c", "sleep 300"],
        labels=LAB_LABEL,
    )
    container.reload()
    print(f"✅ Erstellt: {container.name} | status={container.status}")

    explain("Jetzt starten wir den Container …")
    container.start()
    wait_until_running(container)
    print(f"✅ Läuft:    {container.name} | status={container.status}")

    explain(
        "Wir schreiben eine Datei IN den Container (in seine eigene Schreib-Schicht). "
        "Wichtig: Das ist NICHT dasselbe wie ein Volume."
    )
    code, out = sh(container, "sh -c 'echo \"Hallo aus dem Container\" > /tmp/hallo.txt && cat /tmp/hallo.txt'")
    print("   Ausgabe:", out)

    explain("Jetzt stoppen wir den Container (der Prozess endet).")
    container.stop(timeout=10)
    container.reload()
    print(f"🛑 Gestoppt: {container.name} | status={container.status}")

    explain(
        "Und jetzt starten wir GENAU denselben Container wieder. "
        "Die Datei sollte noch da sein, weil der Container noch existiert."
    )
    pause(no_pause)
    container.start()
    wait_until_running(container)
    code, out = sh(container, "cat /tmp/hallo.txt")
    print("   Datei noch da? ->", out)

    explain(
        "Jetzt kommt der wichtige Teil: Wir löschen den Container. "
        "Damit ist seine eigene Schreib-Schicht weg."
    )
    pause(no_pause)
    container.stop(timeout=10)
    container.remove(force=True)
    print("🗑️  Container gelöscht.")

    explain(
        "Wenn wir jetzt einen NEUEN Container starten, ist /tmp/hallo.txt nicht mehr da. "
        "(Weil es kein Volume war.)"
    )
    pause(no_pause)

    tmp = client.containers.run(
        IMG_ALPINE,
        command=["sh", "-c", "cat /tmp/hallo.txt || echo 'Datei nicht gefunden (neuer Container)'"],
        remove=True,
        labels=LAB_LABEL,
    )
    # tmp ist output (bytes) wenn detach=False. docker-py gibt bytes zurück.
    if isinstance(tmp, (bytes, bytearray)):
        print(tmp.decode("utf-8", errors="replace").strip())
    else:
        print(tmp)

    pause(no_pause)


# ----------------------------
# Schritt: Ports + ENV
# ----------------------------

def step_ports_and_env(client: docker.DockerClient, no_pause: bool) -> None:
    title("Demo 2: Ports veröffentlichen + ENV übergeben")

    ensure_image(client, IMG_NGINX)
    safe_remove_container(client, NAME_NGINX)

    host_port = pick_free_port(8080)

    explain(
        "Wir starten einen Nginx-Webserver im Container (Container-Port 80). "
        f"Wir veröffentlichen ihn auf deinem Host-Port {host_port}."
    )

    pause(no_pause)

    web = client.containers.run(
        IMG_NGINX,
        name=NAME_NGINX,
        detach=True,
        ports={"80/tcp": host_port},
        labels=LAB_LABEL,
    )
    wait_until_running(web)

    print(f"✅ Web-Container läuft: {NAME_NGINX}")
    print(f"   Host-Port: {host_port}  ->  Container-Port: 80")

    explain(
        "Wenn alles klappt, kannst du jetzt im Browser öffnen:\n"
        f"  http://localhost:{host_port}\n"
        "Das Skript versucht auch kurz, die Seite abzurufen."
    )

    # Mini-Test per Python (optional)
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{host_port}", timeout=3) as r:
            html = r.read(200).decode("utf-8", errors="replace")
        print("🌐 HTTP-Test ok (erste Zeichen):")
        print(html.replace("\n", " ")[:200] + " …")
    except Exception as e:
        print("🌐 HTTP-Test hat nicht geklappt (nicht schlimm). Detail:", type(e).__name__)

    pause(no_pause)

    explain(
        "ENV (Umgebungsvariablen): Wir starten jetzt einen winzigen Container, "
        "geben eine Variable mit und lesen sie im Container aus."
    )
    pause(no_pause)

    ensure_image(client, IMG_ALPINE)

    env_output = client.containers.run(
        IMG_ALPINE,
        command=["sh", "-c", "echo \"MEIN_NAME=$MEIN_NAME\""],
        environment={"MEIN_NAME": "Docker-Python"},
        remove=True,
        labels=LAB_LABEL,
    )
    if isinstance(env_output, (bytes, bytearray)):
        print("✅ Im Container kam an:", env_output.decode("utf-8", errors="replace").strip())
    else:
        print("✅ Im Container kam an:", env_output)

    explain(
        "Merke: Ports und ENV setzt man beim Erstellen/Starten. "
        "Das sind Konfigurationsdaten des Containers."
    )

    pause(no_pause)


# ----------------------------
# Schritt: Volumes (Bind vs Named)
# ----------------------------

def step_volumes(client: docker.DockerClient, no_pause: bool) -> None:
    title("Demo 3: Volumes – Bind-Mount vs. Named Volume")

    ensure_image(client, IMG_ALPINE)

    # ---- Bind-Mount ----
    explain(
        "Teil A: Bind-Mount.\n"
        "Wir nehmen einen Ordner von deinem PC und hängen ihn in den Container ein.\n"
        "Alles, was der Container in diesen Ordner schreibt, siehst du direkt am Host."
    )
    pause(no_pause)

    host_dir = (Path.cwd() / "dl6_bind_demo").resolve()
    host_dir.mkdir(exist_ok=True)

    # Einmal sauber machen (Datei löschen)
    host_file = host_dir / "von_container.txt"
    if host_file.exists():
        host_file.unlink()

    bind_container = client.containers.run(
        IMG_ALPINE,
        command=["sh", "-c", "echo 'Hallo HOST!' > /data/von_container.txt && ls -l /data && cat /data/von_container.txt"],
        remove=True,
        mounts=[Mount(target="/data", source=str(host_dir), type="bind")],
        labels=LAB_LABEL,
    )

    print("✅ Container hat in /data geschrieben.")
    if isinstance(bind_container, (bytes, bytearray)):
        print(bind_container.decode("utf-8", errors="replace").strip())
    else:
        print(bind_container)

    print()
    print("🔎 Auf deinem PC sollte jetzt die Datei existieren:")
    print(f"   {host_file}")

    if host_file.exists():
        print("   ✅ Ja, Datei ist da. Inhalt:", host_file.read_text(encoding="utf-8").strip())
    else:
        print("   ⚠️ Datei nicht gefunden. (Auf Windows ggf. Rechte/Path prüfen.)")

    pause(no_pause)

    # ---- Named Volume ----
    explain(
        "Teil B: Named Volume.\n"
        "Docker verwaltet den Speicher. Du gibst dem Volume nur einen Namen.\n"
        "Das Volume kann an mehrere Container (nacheinander) gehängt werden."
    )
    pause(no_pause)

    # Volume anlegen (falls schon da, weiterverwenden)
    try:
        vol = client.volumes.get(VOL_NAMED_DEMO)
        print(f"✅ Volume existiert schon: {VOL_NAMED_DEMO}")
    except NotFound:
        vol = client.volumes.create(name=VOL_NAMED_DEMO, labels=LAB_LABEL)
        print(f"✅ Volume erstellt: {VOL_NAMED_DEMO}")

    explain("Wir starten Container #1 und schreiben eine Datei ins Volume …")
    pause(no_pause)

    c1 = client.containers.run(
        IMG_ALPINE,
        name="dl6_volume_writer",
        detach=True,
        command=["sh", "-c", "echo 'Ich bleibe im Volume!' > /data/persist.txt && sleep 60"],
        mounts=[Mount(target="/data", source=VOL_NAMED_DEMO, type="volume")],
        labels=LAB_LABEL,
    )
    wait_until_running(c1)
    code, out = sh(c1, "cat /data/persist.txt")
    print("   Datei in Container #1:", out)

    explain("Jetzt löschen wir Container #1. Das Volume bleibt absichtlich erhalten.")
    pause(no_pause)

    c1.stop(timeout=10)
    c1.remove(force=True)
    print("🗑️  Container #1 gelöscht.")

    explain("Jetzt starten wir Container #2 mit DEMSELBEN Volume und lesen die Datei.")
    pause(no_pause)

    c2_out = client.containers.run(
        IMG_ALPINE,
        command=["sh", "-c", "ls -l /data && cat /data/persist.txt"],
        mounts=[Mount(target="/data", source=VOL_NAMED_DEMO, type="volume")],
        remove=True,
        labels=LAB_LABEL,
    )

    print("✅ Container #2 sieht die Daten aus dem Volume:")
    if isinstance(c2_out, (bytes, bytearray)):
        print(c2_out.decode("utf-8", errors="replace").strip())
    else:
        print(c2_out)

    explain(
        "Merke:\n"
        "- Bind-Mount: Daten liegen in einem Host-Ordner, du siehst sie direkt.\n"
        "- Named Volume: Docker verwaltet den Speicher, Daten bleiben auch nach 'rm'.\n"
        "Beides lebt länger als ein Container."
    )

    pause(no_pause)


# ----------------------------
# Lab: DB-Container + Volume (Redis)
# ----------------------------

def wait_for_redis(container, timeout_s: int = 25) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            code, out = sh(container, "redis-cli ping")
            if code == 0 and "PONG" in out:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError("Redis wurde nicht bereit innerhalb des Timeouts.")


def step_db_volume_lab(client: docker.DockerClient, no_pause: bool) -> None:
    title("30–75: Lab – Redis (DB) + Volume: Daten bleiben nach Container-Löschung")

    ensure_image(client, IMG_REDIS)

    # Ports so wählen, dass es nicht kollidiert
    redis_port = pick_free_port(16379)

    # --- A) Redis OHNE Volume (Daten gehen verloren) ---
    explain(
        "Teil A: Wir starten Redis OHNE Volume.\n"
        "Wir speichern einen Key. Dann löschen wir den Container.\n"
        "Danach starten wir einen neuen Container – und der Key ist weg."
    )
    pause(no_pause)

    safe_remove_container(client, NAME_REDIS_NO_VOL)

    r1 = client.containers.run(
        IMG_REDIS,
        name=NAME_REDIS_NO_VOL,
        detach=True,
        ports={"6379/tcp": redis_port},
        # wichtig: ohne Volume!
        labels=LAB_LABEL,
    )
    wait_until_running(r1)
    wait_for_redis(r1)

    print(f"✅ Redis läuft (ohne Volume) auf localhost:{redis_port}")

    # Key setzen
    code, out = sh(r1, "redis-cli set geheim 'Schoko-Keks'")
    print("SET:", out)
    code, out = sh(r1, "redis-cli get geheim")
    print("GET:", out)

    explain("Jetzt löschen wir den Container (rm).")
    pause(no_pause)

    r1.stop(timeout=10)
    r1.remove(force=True)
    print("🗑️  Container gelöscht.")

    explain("Wir starten neuen Redis-Container (wieder ohne Volume) …")
    pause(no_pause)

    r1b = client.containers.run(
        IMG_REDIS,
        name=NAME_REDIS_NO_VOL,
        detach=True,
        ports={"6379/tcp": redis_port},
        labels=LAB_LABEL,
    )
    wait_until_running(r1b)
    wait_for_redis(r1b)

    code, out = sh(r1b, "redis-cli get geheim")
    print("GET nach Neustart (neuer Container):", out if out else "(leer / nil)")

    explain("➡️ Ergebnis: Ohne Volume sind Daten nach 'rm' weg.")
    pause(no_pause)

    r1b.stop(timeout=10)
    r1b.remove(force=True)

    # --- B) Redis MIT Named Volume (Daten bleiben) ---
    explain(
        "Teil B: Jetzt starten wir Redis MIT einem Named Volume.\n"
        "Wir aktivieren Persistenz über AOF (appendonly).\n"
        "Dann löschen wir den Container und starten einen neuen – Daten bleiben."
    )
    pause(no_pause)

    safe_remove_container(client, NAME_REDIS_WITH_VOL)

    # Volume anlegen (falls noch nicht da)
    try:
        client.volumes.get(VOL_REDIS)
        print(f"✅ Redis-Volume existiert schon: {VOL_REDIS}")
    except NotFound:
        client.volumes.create(name=VOL_REDIS, labels=LAB_LABEL)
        print(f"✅ Redis-Volume erstellt: {VOL_REDIS}")

    r2 = client.containers.run(
        IMG_REDIS,
        name=NAME_REDIS_WITH_VOL,
        detach=True,
        ports={"6379/tcp": redis_port},
        mounts=[Mount(target="/data", source=VOL_REDIS, type="volume")],
        command=["redis-server", "--appendonly", "yes"],
        labels=LAB_LABEL,
    )
    wait_until_running(r2)
    wait_for_redis(r2)

    print(f"✅ Redis läuft (MIT Volume) auf localhost:{redis_port}")

    # Key setzen
    code, out = sh(r2, "redis-cli set geheim 'Schoko-Keks'")
    print("SET:", out)
    code, out = sh(r2, "redis-cli get geheim")
    print("GET:", out)

    explain(
        "WICHTIG: Wir geben Redis kurz Zeit, die Änderung sicher ins Volume zu schreiben."
    )
    time.sleep(2)

    explain("Jetzt löschen wir den Container, ABER NICHT das Volume.")
    pause(no_pause)

    r2.stop(timeout=10)
    r2.remove(force=True)
    print("🗑️  Container gelöscht – Volume bleibt!")

    explain("Neuer Container, gleiches Volume …")
    pause(no_pause)

    r2b = client.containers.run(
        IMG_REDIS,
        name=NAME_REDIS_WITH_VOL,
        detach=True,
        ports={"6379/tcp": redis_port},
        mounts=[Mount(target="/data", source=VOL_REDIS, type="volume")],
        command=["redis-server", "--appendonly", "yes"],
        labels=LAB_LABEL,
    )
    wait_until_running(r2b)
    wait_for_redis(r2b)

    code, out = sh(r2b, "redis-cli get geheim")
    print("GET nach Neustart (neuer Container, gleiches Volume):", out if out else "(leer / nil)")

    explain(
        "➡️ Ergebnis: Mit Named Volume bleiben Daten erhalten, auch wenn der Container gelöscht wird."
    )

    pause(no_pause)

    # Container laufen lassen oder aufräumen? Wir lassen ihn kurz laufen für Inspektion.
    explain(
        "Lass den Redis-Container ruhig kurz laufen. Im nächsten Schritt räumen wir auf."
    )
    pause(no_pause)


# ----------------------------
# Cleanup (Disziplin)
# ----------------------------

def step_cleanup(client: docker.DockerClient, no_pause: bool) -> None:
    title("75–90: Cleanup – Ressourcen bereinigen als Routine")

    list_lab_resources(client)
    print()

    explain(
        "Aufräumen bedeutet: Container stoppen & löschen, und Volumes bewusst behandeln.\n"
        "Wichtig: Wenn du ein Volume NICHT löschst, bleiben die Daten erhalten – das ist "
        "manchmal gewollt (Persistenz), manchmal aber auch Müll."
    )
    pause(no_pause)

    # Container mit Label dl6=true stoppen und entfernen
    containers = client.containers.list(all=True, filters={"label": "dl6=true"})
    if containers:
        print("🧹 Entferne Lab-Container …")
        for c in containers:
            try:
                c.reload()
                if c.status == "running":
                    print(f"  - stop  {c.name}")
                    c.stop(timeout=10)
                print(f"  - rm    {c.name}")
                c.remove(force=True)
            except APIError as e:
                print(f"  ⚠️  Problem bei {c.name}:", e)
    else:
        print("✅ Keine Lab-Container gefunden.")

    print()
    explain("Jetzt die Volumes. ACHTUNG: Wenn du sie entfernst, sind die Daten wirklich weg.")

    try:
        answer = input("👉 Wenn du die Volumes löschen willst, tippe genau YES und drücke ENTER: ").strip()
    except KeyboardInterrupt:
        print("\nAbbruch.")
        return

    if answer == "YES":
        # Volumes, die dieses Skript nutzt
        for vname in [VOL_NAMED_DEMO, VOL_REDIS]:
            safe_remove_volume(client, vname)

        print("✅ Volumes gelöscht.")
    else:
        print("ℹ️  Volumes bleiben bestehen (Persistenz!).")

    print()
    explain(
        "Extra (optional, nur Info):\n"
        "In der Docker-CLI gibt es 'docker system prune'.\n"
        "In Python gibt es ähnliche Funktionen: client.containers.prune(), client.images.prune(), …\n"
        "Nutze Prune mit Vorsicht – es kann mehr löschen als gedacht."
    )

    print()
    list_lab_resources(client)
    pause(no_pause, "Fertig! Drücke ENTER zum Beenden …")


# ----------------------------
# Main
# ----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="DL6 – Docker per Python (Kapitel 5)")
    parser.add_argument(
        "--step",
        choices=["all", "intro", "input", "lifecycle", "ports", "volumes", "db", "cleanup"],
        default="all",
        help="Nur einen Teil ausführen",
    )
    parser.add_argument("--no-pause", action="store_true", help="Keine ENTER-Pausen")
    args = parser.parse_args()

    client = docker_client()

    # Schritte auswählen
    run_all = args.step == "all"

    if run_all or args.step == "intro":
        step_intro(args.no_pause)

    if run_all or args.step == "input":
        step_input(args.no_pause)

    if run_all or args.step == "lifecycle":
        step_container_lifecycle(client, args.no_pause)

    if run_all or args.step == "ports":
        step_ports_and_env(client, args.no_pause)

    if run_all or args.step == "volumes":
        step_volumes(client, args.no_pause)

    if run_all or args.step == "db":
        step_db_volume_lab(client, args.no_pause)

    if run_all or args.step == "cleanup":
        step_cleanup(client, args.no_pause)


if __name__ == "__main__":
    main()