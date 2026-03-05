# FloatChat Ultimate - Windows Startup Script

Write-Host "🌊 Starting FloatChat Ultimate..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Start all services
Write-Host "🐳 Starting Docker services (PostgreSQL, Redis, Ollama, Backend)..." -ForegroundColor Cyan
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if Ollama model is downloaded
Write-Host "🤖 Checking Ollama model..." -ForegroundColor Cyan
$ollamaCheck = docker exec floatchat-ollama ollama list 2>&1 | Select-String "llama2"

if (-not $ollamaCheck) {
    Write-Host "📥 Downloading Llama2 model (this may take a few minutes)..." -ForegroundColor Yellow
    docker exec floatchat-ollama ollama pull llama2
}

Write-Host "✅ Ollama model ready" -ForegroundColor Green

# Ask about data ingestion
$response = Read-Host "Do you want to ingest ARGO data now? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "📊 Starting ARGO data ingestion..." -ForegroundColor Cyan
    docker exec floatchat-backend python data_ingestion/argo_ingestion.py
}

Write-Host ""
Write-Host "✅ FloatChat Ultimate is running!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   - Frontend:      http://localhost:3000"
Write-Host "   - Backend API:   http://localhost:8000"
Write-Host "   - API Docs:      http://localhost:8000/docs"
Write-Host "   - PostgreSQL:    localhost:5432"
Write-Host "   - Redis:         localhost:6379"
Write-Host "   - Ollama:        http://localhost:11434"
Write-Host ""
Write-Host "📝 View logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f backend"
Write-Host ""
Write-Host "🛑 Stop services:" -ForegroundColor Yellow
Write-Host "   docker-compose down"
Write-Host ""
