# El contenedor tendra la imagen python 3.12 slim como base
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# En el contenedor instalamos libreoffice para poder generar documentos word
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Creamos un directorio /app en el contenedor y lo establecemos como directorio de trabajo
WORKDIR /app

# Copiamos el archivo pyproject.toml y el directorio src al contenedor
COPY pyproject.toml ./
COPY src ./src

# Instalamos las dependencias del proyecto usando pip
RUN pip install --no-cache-dir .

# Exponemos el puerto 10000 para que la aplicacion sea accesible desde fuera del contenedor
CMD ["sh", "-c", "uvicorn jira_collector.api:app --host 0.0.0.0 --port ${PORT:-10000}"]