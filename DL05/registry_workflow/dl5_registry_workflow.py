#!/usr/bin/env python3
"""
Author: Markus Ineichen
Markus Ineichen, CC BY 4.0, 2026

DL 5 – Registries & Image‑Workflow (Taggen, Push/Pull, „was ist seriös?“)
Docker wird hier absichtlich über Python gesteuert (docker SDK), nicht über die CLI.

Inhalt:
- Warum Images in Registries gespeichert werden (public vs. private)
- Authentifizierung (Login/Logout) und lokale Docker-Config
- Tags setzen (Versionierung statt "latest")
- Push & Pull in/aus einer Registry (z.B. Docker Hub)
- Mini-Checkliste: „Ist dieses Image seriös?“

Voraussetzungen:
- Docker läuft (Docker Desktop / Docker Engine)
- Python + Paket docker:  pip install docker
"""

from __future__ import annotations

import json
from getpass import getpass
from pathlib import Path
from typing import Tuple

import docker
from docker.errors import APIError, DockerException, ImageNotFound
from docker.utils import parse_repository_tag


# ----------------------------
# Kleine Helfer für Lernende
# ----------------------------

def ask_text(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{hint}: ").strip()
    except EOFError:
        answer = ""
    return answer if answer else default


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "J/n" if default else "j/N"
    try:
        raw = input(f"{prompt} ({hint}): ").strip().lower()
    except EOFError:
        return default
    if not raw:
        return default
    return raw in {"j", "ja", "y", "yes"}


def split_image_ref(image_ref: str) -> Tuple[str, str]:
    """Teilt repo:tag (port-sicher). Kein Tag => 'latest'."""
    repository, tag = parse_repository_tag(image_ref)
    if not repository:
        raise ValueError(f"Ungültiger Image-Name: {image_ref!r}")
    return repository, tag or "latest"


def print_step(title: str) -> None:
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))


# ----------------------------
# Docker-Aktionen (via Python)
# ----------------------------

def connect_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as exc:
        raise SystemExit(
            "Konnte nicht mit Docker verbinden.\n"
            "Check:\n"
            " - Läuft Docker?\n"
            " - Hast du Berechtigung auf Docker?\n"
            f"Technische Info: {exc}"
        )


def pull_with_progress(client: docker.DockerClient, image_ref: str) -> str:
    repo, tag = split_image_ref(image_ref)
    print(f"Pull: {repo}:{tag}")

    try:
        stream = client.api.pull(repo, tag=tag, stream=True, decode=True)
        for entry in stream:
            if entry.get("error"):
                raise RuntimeError(entry["error"])
            status = entry.get("status")
            progress = entry.get("progress")
            if status:
                msg = f"{status} {progress or ''}".strip()
                print("  -", msg)
    except APIError as exc:
        raise SystemExit(f"Pull fehlgeschlagen: {exc.explanation}") from exc

    return f"{repo}:{tag}"


def tag_image(client: docker.DockerClient, source_ref: str, target_ref: str) -> str:
    src_repo, src_tag = split_image_ref(source_ref)
    tgt_repo, tgt_tag = split_image_ref(target_ref)

    try:
        image = client.images.get(f"{src_repo}:{src_tag}")
    except ImageNotFound as exc:
        raise SystemExit(f"Quell-Image nicht gefunden: {source_ref}") from exc

    ok = image.tag(repository=tgt_repo, tag=tgt_tag)
    if not ok:
        raise SystemExit("Tagging hat nicht geklappt (Docker API lieferte False).")

    print(f"Neuer Tag: {tgt_repo}:{tgt_tag}")
    return f"{tgt_repo}:{tgt_tag}"


def login_registry(client: docker.DockerClient, registry_input: str, username: str, secret: str) -> str:
    # Docker Hub wird intern oft als https://index.docker.io/v1/ geführt.
    registry = "https://index.docker.io/v1/" if registry_input in {"", "docker.io", "index.docker.io"} else registry_input

    try:
        result = client.login(username=username, password=secret, registry=registry, reauth=True)
    except APIError as exc:
        raise SystemExit(f"Login fehlgeschlagen: {exc.explanation}") from exc

    status = result.get("Status") or result.get("status") or str(result)
    print("Login:", status)
    return registry


def push_with_progress(client: docker.DockerClient, image_ref: str) -> None:
    repo, tag = split_image_ref(image_ref)
    print(f"Push: {repo}:{tag}")

    try:
        stream = client.api.push(repo, tag=tag, stream=True, decode=True)
        for entry in stream:
            err = entry.get("error") or entry.get("errorDetail", {}).get("message")
            if err:
                raise RuntimeError(err)
            status = entry.get("status")
            progress = entry.get("progress")
            digest = entry.get("digest")
            if digest:
                print("  - digest:", digest)
            elif status:
                msg = f"{status} {progress or ''}".strip()
                print("  -", msg)
    except APIError as exc:
        raise SystemExit(f"Push fehlgeschlagen: {exc.explanation}") from exc


def logout_registry(client: docker.DockerClient, registry: str) -> None:
    try:
        client.api.logout(registry=registry)
        print("Logout: OK")
    except Exception as exc:
        print("Logout nicht bestätigt (nicht kritisch):", exc)


def show_docker_config_summary() -> None:
    """Zeigt, wo Docker Login-Daten cached (ohne Secrets auszugeben!)."""
    config_path = Path.home() / ".docker" / "config.json"
    print("Docker-Config:", config_path)

    if not config_path.exists():
        print("  (Noch keine config.json gefunden.)")
        return

    try:
        data = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        print("  (Konnte config.json nicht lesen):", exc)
        return

    auths = data.get("auths", {})
    if not auths:
        print("  auths: (leer)")
        return

    print("  auths-Einträge (ohne Secrets):")
    for key, value in auths.items():
        has_auth = "auth" in value
        has_token = "identitytoken" in value or "identityToken" in value
        print(f"   - {key}  (auth={has_auth}, token={has_token})")


def search_images(client: docker.DockerClient) -> None:
    term = ask_text("Suchbegriff", default="node")
    try:
        results = client.images.search(term)
    except APIError as exc:
        print("Suche fehlgeschlagen:", exc.explanation)
        return

    results = sorted(results, key=lambda r: int(r.get("star_count") or 0), reverse=True)[:10]
    print(f"\nTop 10 für {term!r}:")
    print(f"{'NAME':35} {'STARS':>6} {'OFF':>4} {'AUTO':>4}  DESCRIPTION")
    print("-" * 90)
    for r in results:
        name = str(r.get("name") or "")[:35]
        stars = int(r.get("star_count") or 0)
        off = "OK" if r.get("is_official") else "-"
        auto = "OK" if r.get("is_automated") else "-"
        desc = str(r.get("description") or "").replace("\n", " ")
        desc = (desc[:40] + "…") if len(desc) > 41 else desc
        print(f"{name:35} {stars:6d} {off:>4} {auto:>4}  {desc}")


def inspect_image(client: docker.DockerClient, image_ref: str) -> None:
    repo, tag = split_image_ref(image_ref)
    image = client.images.get(f"{repo}:{tag}")
    attrs = image.attrs

    size_bytes = int(attrs.get("Size") or 0)
    created = str(attrs.get("Created") or "")
    user = str((attrs.get("Config") or {}).get("User") or "")
    labels = (attrs.get("Config") or {}).get("Labels") or {}

    print("\nInspect (Kurz):")
    print("  Ref:     ", f"{repo}:{tag}")
    print("  ImageID: ", (attrs.get("Id") or image.id).replace("sha256:", "")[:12])
    print("  Size:    ", f"{size_bytes/1024/1024:.1f} MiB")
    print("  Created: ", created[:19], "…" if created else "")
    print("  User:    ", repr(user), "(leer = oft root)")
    print("  Labels:  ", len(labels))


# ----------------------------
# Hauptprogramm (DL5 Flow)
# ----------------------------

def main() -> None:
    print_step("DL5 – Registries & Image‑Workflow (Docker via Python)")
    client = connect_client()
    print("Docker Verbindung: OK\n")

    print_step("1: Warum kein 'latest' als Strategie?")
    print("Merke: 'latest' ist nur ein Tag-Name. Er kann später auf ein anderes Image zeigen.")
    print("Besser: feste Versionen taggen (z.B. 1.0, 18.13.0, 2026-02-13).")

    print_step("2: Public vs. Private Registry + Tags (kurz)")
    print("Registry = Server für Images. Repository = 'Ordner'. Tag = Versionsetikett.")
    print("Push = hochladen, Pull = herunterladen.\n")

    print_step("Mini: Image suchen (wie 'docker search', aber in Python)")
    search_images(client)

    print_step("3: Übung – Pull → Tag → (optional) Login → Push → Pull")
    source_default = "hello-world:latest"
    source_ref = ask_text("Welches Image pullen?", default=source_default)
    source_ref = pull_with_progress(client, source_ref)
    inspect_image(client, source_ref)

    print("\nTaggen: Wir machen aus dem Image einen eigenen, 'sauberen' Tag.")
    username = ask_text("Docker Hub Username (Enter = ohne Push)", default="")
    target_ref = ""

    if username:
        repo_name = ask_text("Neuer Repository-Name", default="dl5-hello-world")
        tag = ask_text("Neuer Tag (Version, nicht 'latest')", default="1.0")
        target_ref = f"{username}/{repo_name}:{tag}"
        target_ref = tag_image(client, source_ref, target_ref)
        inspect_image(client, target_ref)

    do_push = bool(username) and ask_yes_no("Willst du jetzt wirklich login + push + pull testen?", default=False)
    if do_push and target_ref:
        registry_input = ask_text("Registry (Enter = Docker Hub)", default="")
        secret = getpass("Passwort oder Token (unsichtbar): ").strip()
        registry = login_registry(client, registry_input, username=username, secret=secret)

        print("\nInfo: Docker cached Login-Daten lokal (ohne Verschlüsselung).")
        show_docker_config_summary()

        push_with_progress(client, target_ref)

        if ask_yes_no("Lokal löschen, um Pull zu testen?", default=False):
            repo, tag = split_image_ref(target_ref)
            try:
                client.images.remove(f"{repo}:{tag}")
                print("Lokal gelöscht.")
            except APIError as exc:
                print("Konnte nicht löschen:", exc.explanation)

        print("\nPull-Test (aus der Registry):")
        pull_with_progress(client, target_ref)

        if ask_yes_no("Logout durchführen?", default=True):
            logout_registry(client, registry)
    else:
        print("\nPush/Pull-Test übersprungen (Demo-Modus).")

    print_step("4: Kurzauftrag – Image‑Checkliste")
    checklist_ref = target_ref or source_ref
    inspect_image(client, checklist_ref)

    print("\nBeantworte kurz (für dein Heft) – Beispiel: python:3.12-slim")
    print("1) Quelle: Ist 'python:3.12-slim' ein Official Image auf Docker Hub?")
    print("   Von welcher Organisation stammt es?")

    print("2) Maintainer: Wer pflegt dieses Image?")
    print("   Gibt es ein öffentliches GitHub-Repository mit Dockerfile?")

    print("3) Tag: Warum verwenden wir '3.12-slim' statt 'latest'?")
    print("   Welche konkrete Python-Version wird damit festgelegt?")

    print("4) Risiken prüfen:")
    print("   - Wie gross ist das Image?")
    print("   - Läuft der Container als root? (docker run --rm python:3.12-slim whoami)")
    print("   - Gibt es unbekannte Labels oder Downloads im Dockerfile?")

    print("\nFertig! 👍")


if __name__ == "__main__":
    main()