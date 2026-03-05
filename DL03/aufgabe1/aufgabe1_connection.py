import docker

def main():
    try:
        # Verbindung zu Docker herstellen
        client = docker.from_env()

        # Verbindung testen
        if client.ping():
            print("✅ Verbindung zu Docker klappt.")
        else:
            print("❌ Docker antwortet nicht.")
            return

    except Exception as error:
        print("❌ Keine Verbindung zu Docker.")
        print("Tipp: Ist Docker gestartet?")
        print("Fehler:", error)
        return

    # Docker-Informationen abrufen
    info = client.version()

    print("\n--- Docker-Infos ---")
    print("Docker-Version:", info.get("Version"))
    print("Betriebssystem:", info.get("Os"))
    print("Architektur:", info.get("Arch"))

if __name__ == "__main__":
    main()