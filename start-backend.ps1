# Start FloatChat backend. Script lives in floatchat-ultimate, so backend = same folder\backend
# Run from anywhere: .\floatchat-ultimate\start-backend.ps1  or from floatchat-ultimate: .\start-backend.ps1

$BackendDir = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path (Join-Path $BackendDir "main.py"))) {
    Write-Host "ERROR: main.py not found in $BackendDir"
    exit 1
}
Set-Location $BackendDir
Write-Host "Backend folder: $BackendDir"
Write-Host "API: http://localhost:8000  |  Docs: http://localhost:8000/docs"
Write-Host ""

# Local stack defaults (if not already provided)
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat"
}
if (-not $env:OLLAMA_BASE_URL) {
    $env:OLLAMA_BASE_URL = "http://localhost:11434"
}
if (-not $env:OLLAMA_MODEL) {
    $env:OLLAMA_MODEL = "mistral"
}
if (-not $env:RAG_ENABLED) {
    $env:RAG_ENABLED = "true"
}
if (-not $env:QDRANT_URL) {
    $env:QDRANT_URL = "http://localhost:6333"
}
if (-not $env:QDRANT_COLLECTION) {
    $env:QDRANT_COLLECTION = "ocean_knowledge"
}

Write-Host "DATABASE_URL=$($env:DATABASE_URL)"
Write-Host "OLLAMA_BASE_URL=$($env:OLLAMA_BASE_URL)"
Write-Host "OLLAMA_MODEL=$($env:OLLAMA_MODEL)"
Write-Host "RAG_ENABLED=$($env:RAG_ENABLED)"
Write-Host "QDRANT_URL=$($env:QDRANT_URL)"
Write-Host "QDRANT_COLLECTION=$($env:QDRANT_COLLECTION)"

try {
    $null = Invoke-RestMethod -Uri "$($env:OLLAMA_BASE_URL)/api/tags" -Method GET -TimeoutSec 3
    Write-Host "Ollama check: reachable" -ForegroundColor Green
}
catch {
    Write-Host "Ollama check: unreachable at $($env:OLLAMA_BASE_URL). Start Ollama service first." -ForegroundColor Yellow
}

if ($env:RAG_ENABLED -match '^(1|true|yes|on)$') {
    try {
        $null = Invoke-RestMethod -Uri "$($env:QDRANT_URL)/collections" -Method GET -TimeoutSec 3
        Write-Host "Qdrant check: reachable" -ForegroundColor Green
    }
    catch {
        Write-Host "Qdrant check: unreachable at $($env:QDRANT_URL). RAG will run in lexical fallback mode." -ForegroundColor Yellow
    }
}

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
