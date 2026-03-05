# 01_image_basics

Dieses Beispiel zeigt die **Grundidee von Docker Images und Containern**.

Ein **Image** ist eine Vorlage für einen Container.
Aus einem Image kann ein **Container gestartet werden**, der dann als Prozess läuft.

---

# Dockerfile

Das Image wird mit folgendem Dockerfile gebaut:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY app.py .

CMD ["python", "app.py"]
```

## Erklärungen

### FROM

```dockerfile
FROM python:3.12-slim
```

Das Image basiert auf einem **Base Image**.
Hier wird ein minimales Python-Image verwendet, das bereits Python installiert hat.
Dieses Base Image enthält bereits mehrere **Layer**.

---

### WORKDIR

```dockerfile
WORKDIR /app
```

Setzt das **Arbeitsverzeichnis im Container**. 
Alle folgenden Befehle werden relativ zu diesem Ordner ausgeführt.
Falls das Verzeichnis noch nicht existiert, wird es automatisch erstellt.

---

### COPY

```dockerfile
COPY app.py .
```

Kopiert die Datei `app.py` aus dem Projektordner in das Image.
Der Punkt (`.`) bedeutet:
→ kopiere die Datei in das aktuelle Arbeitsverzeichnis (`/app`).

---

### CMD

```dockerfile
CMD ["python", "app.py"]
```

Definiert den **Standardbefehl beim Start des Containers**.

Beim Start des Containers wird daher ausgeführt:

```
python app.py
```

Dieser Prozess wird zum **Hauptprozess des Containers (PID 1)**.

Solange dieser Prozess läuft, läuft auch der Container.

---

# Image bauen

```bash
docker build -t demo-image .
```

---

# Container starten

```bash
docker run demo-image
```

---

# Hauptprozess im Container

Ein Container führt normalerweise **einen Hauptprozess** aus.
Dieser Prozess wird über `CMD` oder `ENTRYPOINT` definiert.

Im Beispiel ist das:

```
python app.py
```

Dieser Prozess läuft als **PID 1 im Container**.

Wenn dieser Prozess endet, **stoppt auch der Container**.

---

# Hauptprozess überprüfen

### Im Container

```bash
docker exec -it <container-id> cat /proc/1/cmdline
```

Dies zeigt den Befehl des Hauptprozesses.

---

### Vom Host aus

```bash
docker top <container-id>
```

Zeigt die laufenden Prozesse im Container.

---

# Docker Layers

Docker Images bestehen aus **mehreren Layern (Schichten)**.

Jede Dockerfile-Anweisung erzeugt normalerweise einen neuen Layer.

In diesem Dockerfile entstehen vereinfacht folgende Layer:

```
Base Image        -> FROM python:3.12-slim
Arbeitsverzeichnis -> WORKDIR /app
Datei kopieren     -> COPY app.py .
```

`CMD` erzeugt **keinen eigenen Layer**, da es nur Metadaten für den Containerstart definiert.

---

# Layer anzeigen

Die Layer eines Images können angezeigt werden mit:

```bash
docker history demo-image
```

oder

```bash
docker image history demo-image
```

Docker zeigt dann die einzelnen Build-Schritte und deren Layer an.



---

# Warum sind Layer wichtig?

Layer haben einen grossen Vorteil:

Docker kann **unveränderte Layer wiederverwenden (Cache)**.

Wenn sich z.B. nur `app.py` ändert:

* müssen nur die oberen Layer neu gebaut werden
* die unteren Layer bleiben gleich

Dadurch werden **Docker Builds deutlich schneller**.
