import docker
from docker.errors import NotFound

IMAGE_TAG = "school/hello-api:latest"
CONTAINER_NAME = "hello-api"


def main() -> None:
    client = docker.from_env()

    try:
        client.containers.get(CONTAINER_NAME).remove(force=True)
        print("Container removed.")
    except NotFound:
        print("Container not found.")

    # Image entfernen (optional)
    try:
        client.images.remove(IMAGE_TAG, force=True)
        print("Image removed.")
    except Exception as exc:
        print("Image not removed:", exc)


if __name__ == "__main__":
    main()