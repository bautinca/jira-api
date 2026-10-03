from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.requests import Request

from jira_collector import __version__
from jira_collector.config import Settings
from jira_collector.service import collect

# Creamos la aplicacion FastAPI con el titulo y la version del proyecto
app = FastAPI(title="Jira Kanban Collector", version=__version__)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/")
def home(request: Request):
    """Renderiza la vista para iniciar y descargar la recolección."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Jira Document Merge", "action_url": "/collect-and-download"},
    )

# Endpoint de salud para verificar que la aplicacion esta corriendo correctamente.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jira-kanban-collector"}


# Endpoint /collect que ejecuta la funcion principal collect() que coordina todo el flujo de descarga
# y unificacion de adjuntos de la primera columna del tablero de Jira, usando la configuracion de Settings()
# que obtiene los valores de las variables de entorno
@app.post("/collect")
def collect_attachments() -> dict[str, str | int]:
    """Descarga y unifica los adjuntos de la primera columna de Jira."""
    try:
        result = collect(Settings()) # Aca se ejecuta la funcion principal collect() y el que automatiza todo el flujo de descarga y unificacion de adjuntos de la primera columna del tablero de Jira
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        "status": "completed",
        "issues": result.issues,
        "downloaded": result.downloaded,
        "included": result.included,
        "skipped": result.skipped,
        "output_file": str(result.output_file),
    }

# Este endpoint /collect-and-download ejecuta la funcion collect() y luego retorna el archivo de salida generado para que el usuario pueda descargarlo desde el navegador.
# Basicamente es una combinacion de los endpoints /collect y /output para hacer todo en un unico endpoint.
@app.post("/collect-and-download")
def collect_and_download() -> FileResponse:
    """Procesa los documentos y devuelve el resultado para una vista HTML."""
    try:
        collect(Settings())
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return download_output()


# Agregamos un endpoint para descargar el archivo de salida generado por la ultima recoleccion, si existe. Si no existe, retornamos un error 404.
@app.get("/output")
def download_output() -> FileResponse:
    """Descarga el documento Word generado por la ultima recoleccion."""
    output_file = Settings().output_file # Obtenemos la ruta del archivo de salida
    if not output_file.exists(): # Si no existe entonces retornamos error 404
        raise HTTPException(status_code=404, detail="Todavia no existe un documento generado")
    # Si existe entonces retornamos el archivo de salida como respuesta
    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=output_file.name,
    )
