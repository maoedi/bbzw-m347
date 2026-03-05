# 02_layers

Dieses Beispiel zeigt das **Layer-Prinzip von Docker Images**.

Ein Docker Image besteht aus mehreren **Layern (Schichten)**.
Fast jede Anweisung im Dockerfile erzeugt einen neuen Layer.

Der Vorteil: Docker kann **unveränderte Layer wiederverwenden (Cache)**.
Dadurch werden Builds deutlich schneller.

---

# Dockerfile

Das Image wird mit folgendem Dockerfile gebaut:

```dockerfile
FROM python:3.12-slim

ARG maintainer_email=teacher@example.com

LABEL maintainer=$maintainer_email
LABEL demo="docker-layers"

WORKDIR /app

ENV PORT=8080
ENV WHO="Docker Class"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER 1000

CMD ["python", "app.py"]
```

---

# Erklärung wichtiger Anweisungen

**FROM**

Startet von einem Base Image.

```
FROM python:3.12-slim
```

---

**ARG**

Build-Variable, die nur beim Bauen des Images verfügbar ist.

```
ARG maintainer_email=teacher@example.com
```

Beim Build kann der Wert überschrieben werden:

```
docker build --build-arg maintainer_email=me@example.com -t demo-layers .
```

---

**LABEL**

Metadaten des Images.

```dockerfile
LABEL maintainer=$maintainer_email
```

Labels speichern zusätzliche Informationen über ein Image, z.B.:

* Maintainer
* Version
* Beschreibung

Diese Informationen ändern **nicht das Dateisystem des Containers**, sondern werden als **Image-Metadaten** gespeichert.

Sie können später angezeigt werden mit:

```bash
docker inspect <image>
```

---

**WORKDIR**

Setzt das Arbeitsverzeichnis im Container.

```
WORKDIR /app
```

---

**ENV**

Umgebungsvariablen für die Laufzeit.

```
ENV PORT=8080
ENV WHO="Docker Class"
```

Diese Variablen werden von der Python-Anwendung verwendet.

---

**COPY**

Kopiert Dateien in das Image.

```
COPY requirements.txt .
COPY app.py .
```

---

**RUN**

Führt einen Befehl während des Builds aus.

```
RUN pip install --no-cache-dir -r requirements.txt
```

---

**USER**

Definiert den Benutzer, mit dem Prozesse im Container ausgeführt werden.

```dockerfile
USER 1000
```

Standardmässig laufen viele Container als **root** (Administrator).
Aus Sicherheitsgründen ist es jedoch besser, Container als **normaler Benutzer** laufen zu lassen.

Vorteile:

* geringere Sicherheitsrisiken
* eingeschränkte Rechte im Container
* Best Practice für Produktionssysteme

---

**CMD**

Standardprozess beim Start des Containers.

```
CMD ["python", "app.py"]
```

Dieser Prozess wird zum **Hauptprozess (PID 1)** im Container.

---

# Image bauen

Im Projektordner:

```
docker build -t demo-layers .
```

---

# Layer anzeigen

Die Layer des Images können angezeigt werden mit:

```
docker history demo-layers
```

oder

```
docker image history demo-layers
```

Docker zeigt dann alle Build-Schritte und deren Layer an.

---

# Container starten

```
docker run -p 8080:8080 demo-layers
```

Die Anwendung ist danach erreichbar unter:

```
http://localhost:8080
```

---

# Environment Variablen ändern

Die Anwendung liest Konfiguration aus **Environment Variablen**.
In unserem Beispiel verwendet der Python-Webserver die Variablen:

* `WHO` → bestimmt den Namen in der Begrüssung
* `PORT` → bestimmt den Port des Servers

Im Code wird die Variable so ausgelesen:

```python
os.environ.get("WHO", "World")
```

Wenn keine Variable gesetzt ist, wird der Standardwert **"World"** verwendet.

---

## Container mit Environment Variable starten

Beispiel:

```
docker run -p 8080:8080 -e WHO="M347 Students" demo-layers
```

* `-e` → setzt eine Environment Variable im Container
* `WHO="M347 Students"` → wird an den Container übergeben

Die Anwendung ist danach erreichbar unter:

```
http://localhost:8080
```

Antwort des Servers:

```
Hallo M347 Students.
```

Der Webserver liest also die Environment Variable `WHO` aus und verwendet sie in der Antwort.

---

## Environment Variablen im Container anzeigen

Man kann die gesetzten Variablen auch direkt im Container überprüfen.

### Container-ID herausfinden

```
docker ps
```

### Environment Variablen anzeigen

```
docker exec -it <container-id> env
```

Beispielausgabe:

```
WHO=M347 Students
PORT=8080
```

Damit sieht man, dass die Variable tatsächlich im Container gesetzt wurde.

---

## Shell im Container öffnen

Mit folgendem Befehl kann eine **interaktive Shell im Container** gestartet werden:

```
docker exec -it <container-id> /bin/sh
```

Dann befindet man sich direkt im Container und kann dort Befehle ausführen.

Beispiele:

```
env
whoami
ls
```

Die Shell kann mit `exit` wieder verlassen werden.

---

## Verbindung zur Anwendung

Der Ablauf ist also:

```
docker run -e WHO="M347 Students"
            │
            ▼
Environment Variable im Container
            │
            ▼
Python Anwendung liest Variable über os.environ
            │
            ▼
Webserver verwendet den Wert in der HTTP-Antwort
```

Damit können Anwendungen **konfiguriert werden, ohne den Code zu ändern**.


# Layer Cache demonstrieren

Docker verwendet einen **Layer Cache**, um Builds zu beschleunigen.

Wenn nur `app.py` geändert wird:

* müssen nur die oberen Layer neu gebaut werden
* frühere Layer bleiben **CACHED**

Image erneut bauen:

```
docker build -t demo-layers .
```

Docker zeigt dann bei unveränderten Schritten häufig:

```
CACHED
```
