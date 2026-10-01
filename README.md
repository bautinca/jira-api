En una terminal se levanta la aplicacion con el comando:
```shell
uvicorn jira_collector.api:app --reload
```

Y en la otra terminal para mandar solicitudes HTTP se las manda con `curl` por ejemplo al endpoint /collect para procesar documentos:
```shell
curl -X POST http://localhost:8000/collect
```

## Ejecucion automatica

Ejecutar el script para que levante aplicacion, mande solicitud HTTP a endpoint /health y luego a /collect y por ultimo cierre la aplicacion
```shell
./run_collect.sh
```