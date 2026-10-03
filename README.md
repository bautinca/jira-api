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

## Ejecucion automatica con Docker Compose

No hace falta entrar dentro de `.venv`. El archivo `compose.yaml` centraliza la configuracion del servicio web: construye la imagen usando el `Dockerfile`, carga `.env`, configura el puerto y monta los directorios locales. El script solo orquesta el ciclo de vida de Docker Compose.

No necesitas instalar dependencias Python en el sistema local. Solo necesitas Docker, Docker Compose v2 y el archivo `.env`. Las carpetas `downloads/` y `output/` las crea automaticamente el script.

```shell
./run_collect.sh
```

El documento generado queda disponible en `output/merged.docx` y los adjuntos en `downloads/`, porque ambas carpetas se montan desde el host al contenedor. El puerto local por defecto es 8000. Para usar otro puerto:

```shell
HOST_PORT=8001 ./run_collect.sh
```

En Windows, instala Docker Desktop y ejecuta el equivalente de PowerShell:

```powershell
.\run_collect.ps1
```

Si PowerShell bloquea la ejecucion del script, habilitala solo para la terminal actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_collect.ps1
```

El script de Windows usa el mismo `compose.yaml`, `Dockerfile`, `.env`, volumenes y puertos. No necesita Python ni dependencias instaladas en Windows.

Tambien puedes administrar el servicio directamente:

```shell
docker compose up --build
docker compose down
```

## Ejecucion servicio web sitio deployado

Ejecutar la siguiente URL con el servicio web de Render `jira-doc-merge` ya desplegado:
```
https://jira-doc-merge.onrender.com/docs
```

Endpoint `/health` chequea el estado del servidor web con la app levantada, endpoint `/collect` inicia el proceso de mergeo de los documentos y el endoint `/output` descarga el documento mergeado localmente 
