# hello-api

Einfache HTTP-API für die Docker-Übung.

Die Anwendung startet einen kleinen HTTP-Server und gibt eine Begrüssung zurück.

## Projektstruktur

```
src/        Quellcode der Anwendung
scripts/    Hilfsskripte für Docker
Dockerfile  Container-Definition
```

## Virtuelle Umgebung aktivieren

Vor dem Start der Anwendung sollte die virtuelle Python-Umgebung aktiviert werden.
Dadurch werden die projektspezifischen Python-Abhängigkeiten verwendet.

```
source .venv/bin/activate
```

Falls die Umgebung noch nicht existiert, kann sie erstellt werden mit:

```
python -m venv .venv
source .venv/bin/activate
```

### 1. Abhängigkeiten installieren

```
pip install -r requirements.txt
```

## Server lokal ausführen

Die Anwendung kann direkt als Python-Modul gestartet werden:

```
cd src
python -m hello_api.app
```

Der HTTP-Server startet anschließend auf Port **8080**.

Test im Browser oder mit curl:

```
http://localhost:8080
```

oder

```
curl http://localhost:8080
```

---

## Docker

Die Anwendung kann auch containerisiert ausgeführt werden.

### 1. Docker Image bauen

```
docker build -t hello-api .
```

### 2. Container starten

```
docker run -p 8080:8080 hello-api
```

Danach ist die Anwendung erreichbar unter:

```
http://localhost:8080
```

---

## Container mit Python-Skripten starten

In dieser Übung kann der Container auch über die bereitgestellten Python-Skripte gesteuert werden.

Container starten:

```
python scripts/docker_lab.py
```

Container stoppen und bereinigen:

```
python scripts/docker_cleanup.py
```

Diese Skripte verwenden das **Docker SDK for Python**, um Container automatisch zu erstellen, zu starten und wieder zu entfernen.

---

## Container stoppen (manuell)

Falls der Container manuell gestartet wurde, kann er so beendet werden:

```
docker ps
docker stop <container_id>
```

oder direkt beim Start automatisch entfernen lassen:

```
docker run --rm -p 8080:8080 hello-api
```

Dabei wird der Container nach dem Beenden automatisch gelöscht.
