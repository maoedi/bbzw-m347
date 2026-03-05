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

```
LABEL maintainer=$maintainer_email
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

Definiert den Benutzer im Container.

```
USER 1000
```

Best Practice: Container nicht als `root` laufen lassen.

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

Die Anwendung liest Konfiguration aus Environment Variablen.

Beispiel:

```
docker run -p 8080:8080 -e WHO="M347 Students" demo-layers
```

Antwort des Servers:

```
Hallo M347 Students.
```

---

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

---

# Idee der Demo

Diese Demo zeigt:

* dass Docker Images aus **mehreren Layern** bestehen
* wie **Dockerfile-Anweisungen Layer erzeugen**
* wie man Layer mit `docker history` anzeigen kann
* wie **Docker Cache Builds beschleunigt**
* wie **ENV Variablen** eine Anwendung konfigurieren
