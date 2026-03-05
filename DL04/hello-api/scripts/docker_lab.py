import fnmatch
import io
import json
import tarfile
import time
from pathlib import Path
from urllib.request import urlopen

import docker
from docker.errors import NotFound

PROJECT_DIR = Path(__file__).resolve().parent
IMAGE_TAG = "school/hello-api:latest"
CONTAINER_NAME = "hello-api"
HOST_PORT = 8080
CONTAINER_PORT = 8080


def docker_context_size_mb(project_dir: Path) -> float:
    """Berechnet die Build-Context-Größe unter Beachtung einer einfachen .dockerignore-Logik."""
    ignore_file = project_dir / ".dockerignore"
    patterns: list[str] = []

    if ignore_file.exists():
        patterns = [
            line.strip()
            for line in ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def is_ignored(rel_posix: str) -> bool:
        # Sehr einfache .dockerignore-Logik:
        # - fnmatch für Patterns wie "*.pyc"
        # - Prefix für Ordner wie "venv"
        for pat in patterns:
            pat = pat.rstrip("/")
            if pat and (
                fnmatch.fnmatch(rel_posix, pat) or rel_posix.startswith(pat + "/")
            ):
                return True
        return False

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in project_dir.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(project_dir).as_posix()
            if is_ignored(rel):
                continue
            tar.add(p, arcname=rel)

    return buf.tell() / 1024 / 1024


def remove_container_if_exists(client: docker.DockerClient, name: str) -> None:
    try:
        container = client.containers.get(name)
    except NotFound:
        return

    container.remove(force=True)


def build_image(client: docker.DockerClient, maintainer_email: str) -> None:
    print(f"Building image '{IMAGE_TAG}' ...")
    start = time.perf_counter()

    # Low-level API: stabiler für Build-Logs
    stream = client.api.build(
        path=str(PROJECT_DIR),
        tag=IMAGE_TAG,
        buildargs={"email": maintainer_email},
        rm=True,
        decode=True,  # decode=True liefert dicts
    )

    for entry in stream:
        if "stream" in entry:
            print(entry["stream"], end="")
        elif "error" in entry:
            raise RuntimeError(entry["error"])

    image = client.images.get(IMAGE_TAG)
    elapsed = time.perf_counter() - start
    print(f"\nBuild finished in {elapsed:.1f}s, image id: {image.short_id}")


def show_image_labels(client: docker.DockerClient) -> None:
    image = client.images.get(IMAGE_TAG)
    labels = (image.attrs.get("Config", {}) or {}).get("Labels", {}) or {}

    print("Image labels:")
    print(json.dumps(labels, indent=2, ensure_ascii=False))


def show_image_layers(client: docker.DockerClient) -> None:
    # ähnlich wie "docker history"
    history = client.api.history(IMAGE_TAG)

    print("Top layers (history):")
    for i, item in enumerate(history[:8], start=1):
        size_mb = item.get("Size", 0) / 1024 / 1024
        created_by = (item.get("CreatedBy") or "").strip()
        print(f"{i:02d}. {size_mb:6.1f} MB {created_by[:80]}")


def run_container(client: docker.DockerClient, who: str) -> None:
    # Im Schritt 8 hier ändern!
    print(f"Starting container '{CONTAINER_NAME}' ...")

    client.containers.run(
        IMAGE_TAG,
        name=CONTAINER_NAME,
        detach=True,
        ports={f"{CONTAINER_PORT}/tcp": HOST_PORT},  # wie "-p 8080:8080"
        environment={"WHO": who, "PORT": str(CONTAINER_PORT)},
    )

    # kurz warten, bis der Server lauscht
    time.sleep(1.0)

    url = f"http://127.0.0.1:{HOST_PORT}/"
    with urlopen(url, timeout=3) as resp:
        body = resp.read().decode("utf-8")

    print("API response:", body.strip())
    print("Container is running in background.")
    print("Stop/Remove later with: python docker_cleanup.py")


def main() -> None:
    client = docker.from_env()

    remove_container_if_exists(client, CONTAINER_NAME)

    print(
        f"Build context size (dockerignore-aware): "
        f"{docker_context_size_mb(PROJECT_DIR):.1f} MB"
    )

    build_image(client, maintainer_email="markus@example.com")
    show_image_labels(client)
    show_image_layers(client)

    run_container(client, who="Sean and Karl")  # Im Schritt 8 hier ändern!


if __name__ == "__main__":
    main()