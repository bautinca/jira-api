#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE_URL="http://${HOST}:${PORT}"
IMAGE_NAME="${IMAGE_NAME:-jira-kanban-collector:local}"
CONTAINER_NAME="${CONTAINER_NAME:-jira-kanban-collector-run}"
LOG_FILE="$(mktemp)"
CONTAINER_ID=""

cleanup() {
    if [[ -n "${CONTAINER_ID}" ]]; then
        docker rm --force "${CONTAINER_ID}" >/dev/null 2>&1 || true
    fi
    rm -f "${LOG_FILE}"
}

trap cleanup EXIT INT TERM

# Verificamos que Docker este instalado y disponible en el PATH
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker no esta instalado o no esta disponible en el PATH." >&2
    exit 1
fi

# Verificamos que exista el archivo .env con la configuracion de Jira
if [[ ! -f "${ROOT_DIR}/.env" ]]; then
    echo "No se encontro ${ROOT_DIR}/.env con la configuracion de Jira." >&2
    exit 1
fi

# Creamos los directorios necesarios para almacenar los archivos descargados y el documento de salida
cd "${ROOT_DIR}"
mkdir -p downloads output

# Construimos la imagen Docker usando el Dockerfile
echo "Construyendo imagen ${IMAGE_NAME}..."
if ! docker build --tag "${IMAGE_NAME}" . >"${LOG_FILE}" 2>&1; then
    echo "No se pudo construir la imagen Docker." >&2
    cat "${LOG_FILE}" >&2
    exit 1
fi

# Levantamos el contenedor Docker a partir de la imagen construida y exponemos el puerto 10000 del contenedor para acceder a la API
echo "Iniciando contenedor en ${BASE_URL}..."
docker rm --force "${CONTAINER_NAME}" >/dev/null 2>&1 || true
CONTAINER_ID="$(docker run --detach \
    --name "${CONTAINER_NAME}" \
    --env-file "${ROOT_DIR}/.env" \
    --env PORT=10000 \
    --publish "${PORT}:10000" \
    --volume "${ROOT_DIR}/downloads:/app/downloads" \
    --volume "${ROOT_DIR}/output:/app/output" \
    "${IMAGE_NAME}")"
    # en los --volume montamos los directorios los directorios locales generados downloads y output al contenedor para que la app pueda escribir los archivos descargados y el documento de salida
    # Es decir, hay una correspondencia entre los directorios locales y los directorios dentro del contenedor output y downloads, de modo que los archivos generados por la app dentro del contenedor se reflejen en el host

# Ya con el contenedor ejecutandose y la app iniciada, verificamos que la API (precisamente en /health) este disponible antes de ejecutar la recoleccion de datos
# Aca como aclaracion mencionamos que el servicio web dentro del contenedor se ejecuta en el puerto 10000, pero desde el host nos conectamos al contenedor a traves del puerto 8000 (o el que se haya configurado en la variable PORT) gracias al mapeo de puertos que hicimos con --publish "${PORT}:10000"
echo "Levantando API en ${BASE_URL}..."
api_ready=false
for attempt in $(seq 1 60); do
    if curl --fail --silent --show-error --max-time 2 "${BASE_URL}/health" >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    if [[ "$(docker inspect --format '{{.State.Running}}' "${CONTAINER_ID}" 2>/dev/null || true)" != "true" ]]; then
        break
    fi
    sleep 1
done

if [[ "${api_ready}" != "true" ]]; then
    echo "La API no pudo iniciarse." >&2
    cat "${LOG_FILE}" >&2
    docker logs "${CONTAINER_ID}" >&2 || true
    exit 1
fi

# Ejecutamos la recoleccion de datos mandando solicitud POST a /collect y esperamos a que termine
echo "API lista. Ejecutando POST /collect..."
if ! curl --fail --silent --show-error --request POST "${BASE_URL}/collect"; then
    echo "La recoleccion fallo." >&2
    docker logs "${CONTAINER_ID}" >&2 || true
    exit 1
fi
echo
echo "Proceso terminado. Cerrando API..."