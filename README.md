## Ejecucion automatica usando la API de la aplicacion (aca si usamos dependencias locales)
En una terminal se levanta la aplicacion con el comando, ojo aca si tenemos que tener dependencias locales instaladas
entrando al entorno virtual .venv:
```shell
uvicorn jira_collector.api:app --reload
```

Y en la otra terminal (no hace falta dentro de .venv) para mandar solicitudes HTTP se las manda con `curl` por ejemplo al endpoint /collect para procesar documentos:
```shell
curl -X POST http://localhost:8000/collect
```

## Ejecucion automatica con Docker

Aca logicamente no hace falta entrar dentro de .venv. El script utiliza el `Dockerfile` del proyecto. Construye la imagen con todas las dependencias, inicia un contenedor, comprueba `/health`, ejecuta `/collect` y finalmente elimina el contenedor.

No necesita activar `.venv` ni instalar las dependencias Python en el sistema local. Solo requiere Docker, el archivo `.env` y las carpetas `downloads/` y `output/` (que las crea automaticamente el script Shell localmente)

```shell
./run_collect.sh
```

El documento generado queda disponible en `output/merged.docx` y los adjuntos en `downloads/`, porque ambas carpetas se montan desde el host al contenedor. El puerto por defecto es 8000, para usar otro puerto:

```shell
PORT=8001 ./run_collect.sh
```

## Ejecucion servicio web sitio deployado

Ejecutar la siguiente URL con el servicio web de Render `jira-doc-merge` ya desplegado:
```
https://jira-doc-merge.onrender.com/docs
```

Endpoint `/health` chequea el estado del servidor web con la app levantada, endpoint `/collect` inicia el proceso de mergeo de los documentos y el endoint `/output` descarga el documento mergeado localmente 
