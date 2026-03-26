
"""
DL7 – Beobachten & Debuggen
==================================================================

Author: Markus Ineichen
Markus Ineichen, CC BY 4.0

Du steuerst Docker nicht über die Kommandozeile, sondern über Python:
    import docker

Dieses Skript zeigt dir typische Debug-Schritte:
- Version & Systeminfo
- Images ziehen (pull)
- Logs lesen
- Inspect (Ports/ENV/Cmd/Health)
- Exec (Befehle im Container) + Prozesse (top)
- Stats (CPU/RAM)
- Healthchecks
- Netzwerk-Grundlagen (networks + network inspect)
- Events (was ist wann passiert?)
- Bonus: container diff & image history

Voraussetzungen:
1) Docker läuft (Docker Desktop oder Docker Engine)
2) Linux-Container (Standard bei Docker Desktop)
3) Python 3.10+
4) Paket installieren:  pip install docker

Start:
    python dl7_debug_lab.py
"""

import socket
import sys
import time

import docker

# Wenn du keine Pausen willst: auf False setzen
INTERACTIVE = True

try:
    from docker.types import Healthcheck
except Exception:
    Healthcheck = None  # sehr alte docker-Pakete


# ---------------------------
# Hilfsfunktionen
# ---------------------------

def hr():
    print("\n" + "-" * 72 + "\n")


def title(text):
    hr()
    print(text)
    hr()


def wait(msg="Drücke ENTER, um weiterzumachen ..."):
    if not INTERACTIVE:
        return
    try:
        input(msg)
    except KeyboardInterrupt:
        print("\nAbbruch durch Strg+C. Cleanup läuft ...")


def find_free_port():
    """Sucht einen freien TCP-Port auf dem Host (127.0.0.1)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def can_connect(host, port, timeout=1.5):
    """True, wenn TCP-Verbindung klappt."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def simple_http_get(host, port, path="/"):
    """Mini-HTTP-Client (ohne Extra-Bibliotheken)."""
    request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n".encode("utf-8")
    with socket.create_connection((host, port), timeout=2.0) as s:
        s.sendall(request)
        data = s.recv(4096)
    first_line = data.splitlines()[0].decode("utf-8", errors="replace")
    return first_line


def human_bytes(num):
    """Bytes schön anzeigen."""
    units = ["B", "KB", "MB", "GB", "TB"]
    step = 1024.0
    i = 0
    while num >= step and i < len(units) - 1:
        num /= step
        i += 1
    return f"{num:.1f} {units[i]}"


def safe_decode(b):
    if b is None:
        return ""
    if isinstance(b, bytes):
        return b.decode("utf-8", errors="replace")
    return str(b)


def remove_container_if_exists(client, name):
    try:
        c = client.containers.get(name)
        c.remove(force=True)
    except docker.errors.NotFound:
        return


def remove_network_if_exists(client, name):
    try:
        n = client.networks.get(name)
        n.remove()
    except docker.errors.NotFound:
        return


def ensure_image(client, image):
    """
    Stellt sicher, dass ein Image vorhanden ist.
    Hinweis: In Schulnetzwerken ohne Internet kann ein Pull fehlschlagen –
    dann muss das Image vorher bereitgestellt sein.
    """
    try:
        client.images.get(image)
        print(f"✅ Image vorhanden: {image}")
    except docker.errors.ImageNotFound:
        print(f"⬇️  Image wird heruntergeladen (pull): {image}")
        client.images.pull(image)
        print("✅ Fertig.")


def connect():
    title("0) Verbindung zu Docker herstellen")
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Docker-Daemon erreichbar.")
        return client
    except Exception as e:
        print("❌ Ich kann Docker nicht erreichen.")
        print("   - Läuft Docker Desktop / Docker Engine?")
        print("   - Hast du Rechte (Linux: docker-Gruppe / sudo)?")
        print("Fehler:", repr(e))
        sys.exit(1)


# ---------------------------
# Kapitel 6: Erkunden
# ---------------------------

def show_version_and_info(client):
    title("1) docker version & system info (über Python)")
    v = client.version()
    info = client.info()

    print("Docker-Version (Auswahl):")
    print("  - Version:", v.get("Version"))
    print("  - API Version:", v.get("ApiVersion"))
    print("  - OS/Arch:", v.get("Os"), "/", v.get("Arch"))
    print()

    print("Server-Info (Auswahl):")
    print("  - Betriebssystem:", info.get("OperatingSystem"))
    print("  - Kernel:", info.get("KernelVersion"))
    print("  - Storage Driver:", info.get("Driver"))
    print("  - Container (gesamt):", info.get("Containers"))
    print("  - Images (gesamt):", info.get("Images"))


def warmup_container_not_reachable(client):
    title("2) Warm-up: Container läuft, aber Dienst ist NICHT erreichbar")

    ensure_image(client, "nginx:alpine")

    host_port = find_free_port()
    print(f"Wir nehmen einen freien Host-Port: {host_port}")
    print("Problem-Szenario: Wir starten nginx – aber OHNE Port-Weiterleitung.")
    print("Erwartung: Container läuft, aber auf dem Host ist nichts erreichbar.")

    broken_name = "dl7-warmup-broken"
    fixed_name = "dl7-warmup-fixed"
    remove_container_if_exists(client, broken_name)
    remove_container_if_exists(client, fixed_name)

    broken = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=broken_name,
        labels={"dl7": "warmup"},
    )
    time.sleep(1.5)
    broken.reload()

    print("\n✅ Container gestartet:", broken.name, "(Status:", broken.status, ")")
    print("Test: Kann der Host zu 127.0.0.1:", host_port, "verbinden?")
    print("Ergebnis:", "✅ erreichbar" if can_connect("127.0.0.1", host_port) else "❌ NICHT erreichbar")

    hr()
    print("Jetzt debuggen wir SYSTEMATISCH:")

    # 1) Logs
    print("\n1) Logs lesen (stdout/stderr vom Container):")
    # Wir erzeugen extra einen Request innerhalb des Containers, damit ein Logeintrag entsteht.
    _ = broken.exec_run(["sh", "-c", "busybox wget -qO- http://127.0.0.1 >/dev/null || true"])
    logs = safe_decode(broken.logs(tail=20)).strip()
    print(logs or "(Keine Logs sichtbar – je nach Image/Setup möglich.)")

    # 2) Inspect
    print("\n2) Inspect (Konfiguration anschauen):")
    broken.reload()
    ports = broken.attrs.get("NetworkSettings", {}).get("Ports")
    cmd = broken.attrs.get("Config", {}).get("Cmd")
    env = broken.attrs.get("Config", {}).get("Env", [])
    print("  - Cmd (Startbefehl):", cmd)
    print("  - Anzahl ENV-Variablen:", len(env))
    print("  - Port-Mappings:", ports)

    # 3) Exec & Prozesscheck
    print("\n3) Exec: In den Container schauen (Prozesse / Test im Container):")
    res = broken.exec_run(["sh", "-c", "ps"])
    print("ps im Container:\n", safe_decode(res.output))
    res2 = broken.exec_run(["sh", "-c", "busybox wget -S -O- http://127.0.0.1 2>&1 | head -n 3"])
    print("HTTP-Test *im Container* (erste Zeilen):\n", safe_decode(res2.output))

    # 4) Netzwerkcheck
    print("\n4) Netzwerkcheck: In welchem Netzwerk hängt der Container?")
    networks = list(broken.attrs.get("NetworkSettings", {}).get("Networks", {}).keys())
    ip = broken.attrs.get("NetworkSettings", {}).get("IPAddress")
    print("  - Netzwerke:", networks)
    print("  - Container-IP (Linux-Bridge):", ip)

    hr()
    print("👉 Diagnose:")
    print("Der Dienst läuft im Container (wget zu 127.0.0.1 klappt),")
    print("aber der Host sieht ihn nicht, weil KEIN Port veröffentlicht wurde.")

    hr()
    print("✅ Fix: Wir starten den Container neu – diesmal mit Port-Weiterleitung.")
    broken.remove(force=True)

    fixed = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=fixed_name,
        labels={"dl7": "warmup"},
        ports={"80/tcp": host_port},  # <- DAS ist der Fix
    )
    time.sleep(1.5)
    fixed.reload()

    print("Neuer Container:", fixed.name)
    print("Inspect Port-Mappings:", fixed.attrs.get("NetworkSettings", {}).get("Ports"))

    try:
        print("HTTP-Test vom Host:", simple_http_get("127.0.0.1", host_port))
    except Exception as e:
        print("❌ Host-HTTP-Test ging schief:", repr(e))
        print("   Tipp: Prüfe Port-Belegung/Firewall.")

    print("\nCleanup: Warm-up-Container entfernen.")
    fixed.remove(force=True)


# ---------------------------
# Stationenlernen (4 Stationen)
# ---------------------------

def station_logs(client):
    title("3) Station 1: Logs lesen (Fehlermeldungen finden)")

    ensure_image(client, "alpine:3.20")

    name = "dl7-logs"
    remove_container_if_exists(client, name)

    print("Wir starten einen Mini-Container, der 'INFO' und 'ERROR' schreibt.")
    c = client.containers.run(
        "alpine:3.20",
        command=["sh", "-c", "echo 'INFO: Start'; echo 'ERROR: Konfiguration fehlt!' 1>&2; echo 'INFO: Ich laufe...'; sleep 8"],
        detach=True,
        name=name,
        labels={"dl7": "logs"},
    )
    time.sleep(0.8)

    print("\nAufgabe: Finde die ERROR-Zeile in den Logs.")
    print("Logs (tail=20):")
    print(safe_decode(c.logs(tail=20)))

    print("Live-Logs (follow) für 3 Sekunden:")
    start = time.time()
    for chunk in c.logs(stream=True, follow=True):
        print(safe_decode(chunk), end="")
        if time.time() - start > 3:
            break

    c.remove(force=True)


def station_inspect(client):
    title("4) Station 2: Inspect (Ports/ENV)")

    ensure_image(client, "nginx:alpine")

    host_port = find_free_port()
    name = "dl7-inspect"
    remove_container_if_exists(client, name)

    c = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=name,
        labels={"dl7": "inspect"},
        environment={"APP_MODE": "demo", "APP_PORT": "80"},
        ports={"80/tcp": host_port},
    )
    time.sleep(1.2)
    c.reload()

    print("Aufgabe: Finde heraus ...")
    print("  a) Welche ENV-Variablen wurden gesetzt?")
    print("  b) Welcher Host-Port ist gemappt?")
    print()

    env = c.attrs.get("Config", {}).get("Env", [])
    ports = c.attrs.get("NetworkSettings", {}).get("Ports", {})

    app_env = [e for e in env if e.startswith("APP_")]
    print("a) APP_-ENV-Variablen:", app_env)

    mapping = ports.get("80/tcp", [])
    host_port_seen = mapping[0]["HostPort"] if mapping else "?"
    print("b) Port-Mapping 80/tcp -> HostPort:", host_port_seen)

    print("\nCheck: Host-HTTP-Test:", simple_http_get("127.0.0.1", int(host_port_seen)))

    c.remove(force=True)


def station_exec_and_processes(client):
    title("5) Station 3: Exec & Prozesscheck (läuft mein Prozess wirklich?)")

    ensure_image(client, "ubuntu:22.04")

    name = "dl7-exec"
    remove_container_if_exists(client, name)

    c = client.containers.run(
        "ubuntu:22.04",
        command=["sleep", "60"],  # Top-Level-Prozess ist "sleep"
        detach=True,
        name=name,
        labels={"dl7": "exec"},
    )
    time.sleep(1.0)

    print("Wir führen Befehle IM laufenden Container aus (exec_run).")
    print("\n1) ps -ef (Prozesse im Container):")
    res = c.exec_run(["sh", "-c", "ps -ef | head -n 20"])
    print(safe_decode(res.output))

    print("2) Wer ist PID 1?")
    res2 = c.exec_run(["sh", "-c", "ps -p 1 -o pid,ppid,cmd"])
    print(safe_decode(res2.output))

    print("3) docker container top-ähnlich (über SDK):")
    top = c.top()
    print("Spalten:", top.get("Titles"))
    for row in top.get("Processes", [])[:5]:
        print(" ", row)

    c.remove(force=True)


def calc_cpu_percent(stat1, stat2):
    """Sehr einfache CPU%-Berechnung aus zwei Stats-Snapshots."""
    try:
        cpu_total1 = stat1["cpu_stats"]["cpu_usage"]["total_usage"]
        cpu_total2 = stat2["cpu_stats"]["cpu_usage"]["total_usage"]
        system1 = stat1["cpu_stats"]["system_cpu_usage"]
        system2 = stat2["cpu_stats"]["system_cpu_usage"]

        cpu_delta = cpu_total2 - cpu_total1
        system_delta = system2 - system1

        percpu = stat2["cpu_stats"]["cpu_usage"].get("percpu_usage") or []
        num_cpus = len(percpu) if percpu else int(stat2["cpu_stats"].get("online_cpus") or 1)

        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * num_cpus * 100.0
    except Exception:
        pass
    return 0.0


def station_stats(client):
    title("6) Input: Stats (CPU/RAM) – wie 'docker container stats'")

    ensure_image(client, "alpine:3.20")

    name = "dl7-stats"
    remove_container_if_exists(client, name)

    c = client.containers.run(
        "alpine:3.20",
        command=["sh", "-c", "while true; do :; done"],  # CPU-Last
        detach=True,
        name=name,
        labels={"dl7": "stats"},
    )
    time.sleep(1.0)

    s1 = c.stats(stream=False)
    time.sleep(1.0)
    s2 = c.stats(stream=False)

    cpu_percent = calc_cpu_percent(s1, s2)

    mem_usage = float(s2["memory_stats"].get("usage", 0))
    mem_limit = float(s2["memory_stats"].get("limit", 1))
    mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit else 0.0

    networks = s2.get("networks") or {}
    rx = tx = 0.0
    for iface in networks.values():
        rx += float(iface.get("rx_bytes", 0))
        tx += float(iface.get("tx_bytes", 0))

    print(f"CPU (≈): {cpu_percent:.1f} %")
    print(f"RAM: {human_bytes(mem_usage)} / {human_bytes(mem_limit)} ({mem_percent:.1f} %)")
    print(f"NET: RX {human_bytes(rx)} / TX {human_bytes(tx)}")

    c.remove(force=True)


def station_healthchecks(client):
    title("7) Input: Healthchecks (healthy/unhealthy)")

    ensure_image(client, "nginx:alpine")

    ok_name = "dl7-hc-ok"
    bad_name = "dl7-hc-bad"
    remove_container_if_exists(client, ok_name)
    remove_container_if_exists(client, bad_name)

    if Healthcheck is None:
        print("⚠️ Dein docker-Python-Paket ist sehr alt. Healthcheck-Demo übersprungen.")
        return

    # Zeiten sind in Nanosekunden
    interval = 2_000_000_000
    timeout = 1_000_000_000
    start_period = 1_000_000_000

    hc_ok = Healthcheck(
        test=["CMD-SHELL", "busybox wget -qO- http://127.0.0.1 >/dev/null || exit 1"],
        interval=interval,
        timeout=timeout,
        retries=3,
        start_period=start_period,
    )

    hc_bad = Healthcheck(
        test=["CMD-SHELL", "busybox wget -qO- http://127.0.0.1:9999 >/dev/null || exit 1"],
        interval=interval,
        timeout=timeout,
        retries=2,
        start_period=start_period,
    )

    c_ok = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=ok_name,
        labels={"dl7": "healthcheck"},
        healthcheck=hc_ok,
    )

    c_bad = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=bad_name,
        labels={"dl7": "healthcheck"},
        healthcheck=hc_bad,
    )

    print("Warte kurz, bis Docker die Healthchecks ausführt ...")
    for i in range(1, 8):
        time.sleep(1.0)
        c_ok.reload()
        c_bad.reload()
        ok_status = (((c_ok.attrs.get("State") or {}).get("Health") or {}).get("Status")) or "?"
        bad_status = (((c_bad.attrs.get("State") or {}).get("Health") or {}).get("Status")) or "?"
        print(f"t={i:02d}s  hc-ok={ok_status:>10}   hc-bad={bad_status:>10}")

    c_ok.remove(force=True)
    c_bad.remove(force=True)


def station_network(client):
    title("8) Station 4: Netzwerkcheck (Networks + Network inspect)")

    ensure_image(client, "alpine:3.20")

    net_name = "dl7-net"
    remove_network_if_exists(client, net_name)

    print("Wir erstellen ein eigenes Bridge-Netzwerk (übersichtlich!).")
    net = client.networks.create(net_name, driver="bridge")

    a_name = "dl7-net-a"
    b_name = "dl7-net-b"
    remove_container_if_exists(client, a_name)
    remove_container_if_exists(client, b_name)

    a = client.containers.run(
        "alpine:3.20",
        command=["sh", "-c", "sleep 60"],
        detach=True,
        name=a_name,
        labels={"dl7": "network"},
        network=net_name,
    )
    b = client.containers.run(
        "alpine:3.20",
        command=["sh", "-c", "sleep 60"],
        detach=True,
        name=b_name,
        labels={"dl7": "network"},
        network=net_name,
    )

    time.sleep(1.0)
    net.reload()

    print("\nNetwork inspect (Auswahl):")
    containers = net.attrs.get("Containers") or {}
    for cid, data in containers.items():
        print(f"  - {data.get('Name')}  IP={data.get('IPv4Address')}  (id={cid[:12]})")

    print("\nTest: Kann Container A Container B per Namen pingen? (DNS im Netzwerk)")
    res = a.exec_run(["sh", "-c", "ping -c 1 dl7-net-b"])
    print(safe_decode(res.output))

    a.remove(force=True)
    b.remove(force=True)
    net.remove()


# ---------------------------
# Extras
# ---------------------------

def station_events(client):
    title("9) Bonus: Events (Was hat Docker wann getan?)")

    ensure_image(client, "debian:latest")

    print("Wir starten einen kurzlebigen Container und lesen danach Events aus.")
    since = int(time.time())
    client.containers.run("debian:latest", command=["sleep", "1"], remove=True)
    until = since + 10

    print("\nEvents (container create/start/die/destroy) im Zeitfenster:")
    events = client.events(decode=True, since=since, until=until)
    shown = 0
    for e in events:
        if e.get("Type") != "container":
            continue
        action = e.get("Action")
        attrs = (e.get("Actor") or {}).get("Attributes") or {}
        name = attrs.get("name", "?")
        image = attrs.get("image", "?")
        print(f"  - {action:>10}   name={name:<12}  image={image}")
        shown += 1
        if shown >= 12:
            break


def bonus_diff_and_history(client):
    title("10) Bonus: container diff & image history")

    ensure_image(client, "nginx:alpine")

    name = "dl7-diff"
    remove_container_if_exists(client, name)

    c = client.containers.run(
        "nginx:alpine",
        detach=True,
        name=name,
        labels={"dl7": "diff"},
    )
    time.sleep(1.5)

    print("container diff: Welche Dateien wurden im Container geändert/angelegt?")
    diff = c.diff()

    kind_map = {0: "CHANGED", 1: "ADDED", 2: "DELETED"}
    for item in diff[:20]:
        k = kind_map.get(item.get("Kind"), str(item.get("Kind")))
        print(f"  - {k:7}  {item.get('Path')}")

    c.remove(force=True)

    img = client.images.get("nginx:alpine")
    hist = img.history()
    print("\nimage history (oberste 5 Layer):")
    for layer in hist[:5]:
        created_by = (layer.get("CreatedBy") or "").strip()
        size = layer.get("Size") or 0
        print(f"  - {human_bytes(float(size)):>10}  {created_by[:60]}")


def debug_checklist():
    title("11) Debug-Checkliste (für eure gemeinsame Liste)")

    checklist = [
        "1) Symptom klären: Was genau geht nicht? (Port? URL? Timeout? Error?)",
        "2) Logs: Gibt es ERRORs in stdout/stderr?",
        "3) Inspect: Image, Cmd/Entrypoint, ENV, Ports, Volumes, Restart, Health-Status",
        "4) Prozesse: Läuft der erwartete Prozess? (top / exec ps)",
        "5) Von innen testen: Funktioniert der Dienst im Container? (exec wget/curl)",
        "6) Stats: CPU/RAM voll? OOM? Zu viele Prozesse?",
        "7) Netzwerk: Welches Netzwerk? Richtige IP/Name? Port-Mapping korrekt?",
        "8) Events: Start/Stop/Restart-Schleife? Fehlerzeitpunkte erkennen.",
        "9) Bonus: diff (schreibt die App ins Dateisystem?) / image history (Base-Image ok?)",
    ]
    for line in checklist:
        print("•", line)


def main():
    client = connect()

    show_version_and_info(client)
    wait()

    warmup_container_not_reachable(client)
    wait()

    station_logs(client)
    wait()

    station_inspect(client)
    wait()

    station_exec_and_processes(client)
    wait()

    station_stats(client)
    wait()

    station_healthchecks(client)
    wait()

    station_network(client)
    wait()

    station_events(client)
    wait()

    bonus_diff_and_history(client)
    wait()

    debug_checklist()
    hr()
    print("Fertig ✅  Tipp: Öffne das Skript und ändere Dinge (Ports, ENV, Commands).")


if __name__ == "__main__":
    main()