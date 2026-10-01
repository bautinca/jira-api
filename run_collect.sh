#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE_URL="http://${HOST}:${PORT}"
PYTHON="${PYTHON:-${ROOT_DIR}/.venv/bin/python}"
LOG_FILE="$(mktemp)"
SERVER_PID=""

cleanup() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
    rm -f "${LOG_FILE}"
}

trap cleanup EXIT INT TERM

if [[ ! -x "${PYTHON}" ]]; then
    echo "No se encontro Python en ${PYTHON}. Crea el entorno con: python3 -m venv .venv" >&2
    exit 1
fi

cd "${ROOT_DIR}"
"${PYTHON}" -m uvicorn jira_collector.api:app --host "${HOST}" --port "${PORT}" >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!

echo "Levantando API en ${BASE_URL}..."
if ! curl --fail --silent --show-error --retry 30 --retry-delay 1 --retry-connrefused "${BASE_URL}/health" >/dev/null; then
    echo "La API no pudo iniciarse." >&2
    cat "${LOG_FILE}" >&2
    exit 1
fi

echo "API lista. Ejecutando POST /collect..."
curl --fail --silent --show-error --request POST "${BASE_URL}/collect"
echo
echo "Proceso terminado. Cerrando API..."