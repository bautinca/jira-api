from collections.abc import Iterator
from typing import Any

import httpx


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            auth=(email, api_token),
            headers={"Accept": "application/json"},
            timeout=60.0,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    # LLAMADA GET A LA API DE JIRA Y DEVUELVE RESPUESTA EN JSON
    # Esta funcion hace una llamada GET a la API de Jira y retorna la respuesta en formato JSON
    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        response = self.client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    # DEVUELVE ESTADOS DE LA PRIMER COLUMNA DEL TABLERO
    # Esta funcion retorna los IDs de los estados de la primera columna del tablero, que se usan para filtrar los issues
    # Por ejemplo la primer columna puede tener los estados "To Do" y "Backlog", y esta funcion retornaria sus IDs para poder filtrar los issues que esten en esos estados
    def first_column_status_ids(self, board_id: int) -> list[str]:
        data = self._get(f"/rest/agile/1.0/board/{board_id}/configuration") # Obtiene la configuracion del tablero
        columns = data.get("columnConfig", {}).get("columns", []) # Obtiene las columnas de la configuracion del tablero
        if not columns:
            raise RuntimeError(f"El tablero {board_id} no tiene columnas configuradas")
        return [str(status["id"]) for status in columns[0].get("statuses", [])] # Retorna los IDs de los estados de la primera columna

    # DEVUELVE LOS ISSUES EN LA PRIMER COLUMNA DEL TABLERO
    # Obtiene las tareas (issues) que estan en la primera columna del tablero
    def issues_in_first_column(self, board_id: int) -> Iterator[dict[str, Any]]:
        status_ids = self.first_column_status_ids(board_id) # Obtenemos los estados de la primer columna
        if not status_ids: # Si no hay estados en la primer columna, retornamos un iterador vacio
            return
        # Generamos una consulta JQL para obtener los issues que esten en los estados de la primer columna
        # Por ejemplo si los estados de la primer columna son "To Do" entonces la consulta JQL seria "status in (To Do) ORDER BY key"
        jql = f"status in ({','.join(status_ids)}) ORDER BY key"
        start_at = 0
        # 'jql' seria la consulta JQL que se le pasa a Jira para filtrar los issues, 'startAt' es el indice del primer issue a retornar, y 'maxResults' es la cantidad maxima de issues a retornar por cada llamada a la API
        while True:
            # En 'data' obtenemos la respuesta de la API de Jira con los issues que cumplen con la consulta JQL, empezando desde el indice 'start_at' y retornando un maximo de 50 issues por llamada
            data = self._get(
                f"/rest/agile/1.0/board/{board_id}/issue",
                jql=jql,
                fields="summary,status,attachment",
                startAt=start_at,
                maxResults=50,
            )
            # Obtenemos los issues de la respuesta de la API de Jira
            issues = data.get("issues", [])
            # Retornamos los issues obtenidos de la respuesta de la API de Jira
            # Por ejemplo podria retornar un issue con la siguiente estructura:
            # {
            #     "id": "10001",
            #     "key": "PROY-1",
            #     "fields": {
            #         "summary": "Titulo de la tarea",
            #         "status": {
            #             "id": "1",
            #             "name": "To Do"
            #         },
            #         "attachment": [
            #             {
            #                 "id": "1001",
            #                 "filename": "archivo.pdf",
            #                 "content": "https://jira.example.com/secure/attachment/1001/archivo.pdf" # Esta seria la URL de descarga del adjunto
            #             }
            #         ]
            #     }
            yield from issues
            if len(issues) < data.get("maxResults", 50):
                return
            start_at += len(issues)

    # DESCARGA UN ADJUNTO DE JIRA A UN DESTINO LOCAL
    # Este metodo descarga un adjunto de Jira a un destino local
    # 'attachment' es un diccionario que contiene la informacion del adjunto, incluyendo la URL de descarga en 'attachment["content"]'
    # 'destination' es un objeto Path que representa la ruta local donde se guardara el adjunto descargado
    # Por ejemplo, si el adjunto es un archivo PDF llamado "archivo.pdf" y el destino es Path("downloads/PROY-1_archivo.pdf"), entonces este metodo descargara el archivo desde la URL de Jira y lo guardara en "downloads/PROY-1_archivo.pdf"
    def download_attachment(self, attachment: dict[str, Any], destination) -> None:
        response = self.client.get(attachment["content"])
        response.raise_for_status()
        destination.write_bytes(response.content)
