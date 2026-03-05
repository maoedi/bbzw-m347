import docker

def main():
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Verbindung zu Docker klappt.\n")
    except Exception as error:
        print("❌ Keine Verbindung zu Docker.")
        print("Tipp: Ist Docker gestartet?")
        print("Fehler:", error)
        return

    print("📥 Lade Image ubuntu:latest ...")
    client.images.pull("ubuntu:latest")
    print("✅ Image bereit.\n")

    command = "bash -lc 'echo Hallo aus dem Container!; whoami; uname -s'"
    output = client.containers.run(
        "ubuntu:latest",
        command,
        remove=True
    )

    print("--- Ausgabe aus dem Container ---")
    print(output.decode().strip())

if __name__ == "__main__":
    main()