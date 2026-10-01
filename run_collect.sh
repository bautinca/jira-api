#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
HOST_PORT="${HOST_PORT:-${PORT:-8000}}"
BASE_URL="http://${HOST}:${HOST_PORT}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-jira-kanban-collector}"
LOG_FILE="$(mktemp)"

cleanup() {
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" down --remove-orphans >/dev/null 2>&1 || true
    rm -f "${LOG_FILE}"
}

trap cleanup EXIT INT TERM

# Verificamos que Docker este instalado y disponible en el PATH
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker no esta instalado o no esta disponible en el PATH." >&2
    exit 1
fi

# Verificamos que docker compose este instalado y disponible en el PATH
if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose no esta disponible. Instala Docker Compose v2." >&2
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

# Construimos e iniciamos el servicio usando compose.yaml y el Dockerfile
echo "Construyendo e iniciando el servicio web en ${BASE_URL}..."
if ! docker compose --project-name "${COMPOSE_PROJECT_NAME}" up --build --detach >"${LOG_FILE}" 2>&1; then
    echo "No se pudo iniciar Docker Compose." >&2
    cat "${LOG_FILE}" >&2
    exit 1
fi

# Esperamos a que la API este lista antes de ejecutar la recoleccion
echo "Esperando a que la API este disponible..."
api_ready=false
for attempt in $(seq 1 60); do
    if curl --fail --silent --show-error --max-time 2 "${BASE_URL}/health" >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    if [[ -z "$(docker compose --project-name "${COMPOSE_PROJECT_NAME}" ps -q web 2>/dev/null)" ]]; then
        break
    fi
    sleep 1
done

if [[ "${api_ready}" != "true" ]]; then
    echo "La API no pudo iniciarse." >&2
    cat "${LOG_FILE}" >&2
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" logs web >&2 || true
    exit 1
fi

# Ejecutamos la recoleccion de datos mandando solicitud POST a /collect y esperamos a que termine
echo "API lista. Ejecutando POST /collect..."
if ! curl --fail --silent --show-error --request POST "${BASE_URL}/collect"; then
    echo "La recoleccion fallo." >&2
    docker compose --project-name "${COMPOSE_PROJECT_NAME}" logs web >&2 || true
    exit 1
fi
echo
echo "Proceso terminado. Cerrando API..."