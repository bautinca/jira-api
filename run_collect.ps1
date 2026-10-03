$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hostAddress = if ($env:HOST) { $env:HOST } else { "127.0.0.1" }
$hostPort = if ($env:HOST_PORT) { $env:HOST_PORT } elseif ($env:PORT) { $env:PORT } else { "8000" }
$baseUrl = "http://${hostAddress}:${hostPort}"
$projectName = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "jira-kanban-collector" }
$composeArgs = @("--project-name", $projectName)

function Stop-Compose {
    & docker compose @composeArgs down --remove-orphans *> $null
}

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker no esta instalado o no esta disponible en el PATH. Instala Docker Desktop."
    }

    & docker compose version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose no esta disponible. Usa Docker Compose v2 incluido en Docker Desktop."
    }

    if (-not (Test-Path (Join-Path $rootDir ".env"))) {
        throw "No se encontro el archivo .env con la configuracion de Jira."
    }

    Set-Location $rootDir
    New-Item -ItemType Directory -Force -Path "downloads", "output" | Out-Null

    Write-Host "Construyendo e iniciando el servicio web en $baseUrl..."
    & docker compose @composeArgs up --build --detach
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo iniciar Docker Compose."
    }

    Write-Host "Esperando a que la API este disponible..."
    $apiReady = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            $health = Invoke-WebRequest -Uri "$baseUrl/health" -Method Get -TimeoutSec 2
            if ($health.StatusCode -eq 200) {
                $apiReady = $true
                break
            }
        }
        catch {
            # La API puede tardar unos segundos en arrancar.
        }

        $serviceId = (& docker compose @composeArgs ps -q web).Trim()
        if ([string]::IsNullOrWhiteSpace($serviceId)) {
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $apiReady) {
        & docker compose @composeArgs logs web
        throw "La API no pudo iniciarse."
    }

    Write-Host "API lista. Ejecutando POST /collect..."
    $result = Invoke-RestMethod -Uri "$baseUrl/collect" -Method Post
    $result | ConvertTo-Json -Compress
    Write-Host "Proceso terminado. Cerrando Docker Compose..."
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Stop-Compose
}