FROM python:3.12-slim

# Build-Argument (nur beim Build verfügbar)
ARG email="student@example.com"

# Labels = Metadaten am Image
LABEL maintainer="${email}"
LABEL app="hello-api"

WORKDIR /app

# Erst "stabile" Dateien kopieren (Cache!)
COPY requirements.txt /app/

# Keine Pakete nötig, aber die Zeile zeigt das typische Muster:
RUN python -m pip install --upgrade pip

# Jetzt kommt der Code (ändert sich häufiger)
COPY src/hello_api/app.py /app/app.py

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]