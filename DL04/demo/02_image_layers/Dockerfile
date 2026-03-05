FROM python:3.12-slim

# Build Argument (nur beim Build verfügbar)
ARG maintainer_email=teacher@example.com

# Metadaten
LABEL maintainer=$maintainer_email
LABEL demo="docker-layers"

# Arbeitsverzeichnis
WORKDIR /app

# Environment Variable für Laufzeit
ENV PORT=8080
ENV WHO="Docker Class"

# Dependencies zuerst kopieren (wichtig für Layer Cache)
COPY requirements.txt .

# Installation der Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Applikationscode
COPY app.py .

# Container läuft nicht als root (Best Practice)
USER 1000

CMD ["python", "app.py"]