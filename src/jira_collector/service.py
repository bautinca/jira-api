from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jira_collector.document_merger import merge_documents
from jira_collector.jira import JiraClient


@dataclass
class CollectionResult:
    issues: int
    downloaded: int
    included: int
    skipped: int
    output_file: Path

# La funcion collect es el que coordina todo el flujo automatizandolo, recibe instancia de Settings
def collect(settings) -> CollectionResult:
    # Crea los directorios de descarga y salida si no existen
    settings.download_dir.mkdir(parents=True, exist_ok=True)
    # Crea el directorio del archivo de salida si no existe
    settings.output_file.parent.mkdir(parents=True, exist_ok=True)
    # Crea un cliente de Jira con la configuracion recibida, recibe la URL base de Jira, el email y el token de API
    client = JiraClient(settings.jira_base_url, settings.jira_email, settings.jira_api_token)
    # Los documentos seran una lista de rutas de archivos descargados que seran procesados por la funcion merge_documents para unirlos en un solo archivo de salida
    documents: list[Path] = []
    issues_count = downloaded = included = skipped = 0
    try:
        for issue in client.issues_in_first_column(settings.jira_board_id): # Usando el cliente de Jira obtenemos los issues de la primer columna del tablero con el metodo issues_in_first_column
            issues_count += 1
            issue_key = issue["key"]
            fields: dict[str, Any] = issue.get("fields", {})
            # Obtenemos los adjuntos del issue, que es una lista de diccionarios con la informacion de cada adjunto
            attachments = fields.get("attachment", [])
            for attachment in attachments:
                # Del adjunto obtenemos el nombre original del archivo y creamos un destino local para guardarlo, usando el nombre del issue y el nombre del archivo
                original_name = Path(attachment["filename"]).name
                destination = settings.download_dir / f"{issue_key}_{original_name}"
                # Descargamos el adjunto usando el cliente de Jira y el metodo download_attachment
                # El metodo download_attachment recibe el diccionario del adjunto y el destino local donde se guardara el archivo descargado
                client.download_attachment(attachment, destination)
                downloaded += 1
                if destination.suffix.lower() not in {".doc", ".docx"}:
                    skipped += 1
                    continue
                documents.append(destination)
    # Finalmente cerramos el cliente de Jira para liberar recursos
    finally:
        client.close()
    # Una vez descargados todos los adjuntos de los issues de la primer columna, llamamos a la funcion merge_documents para unirlos en un solo archivo de salida
    included = merge_documents(documents, settings.output_file)
    return CollectionResult(issues_count, downloaded, included, skipped, settings.output_file)
