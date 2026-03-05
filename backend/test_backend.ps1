# Test script for FloatChat Ultimate Backend
# Run this in a NEW terminal while the backend is running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FloatChat Ultimate - Backend Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Test 1: Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend is running!" -ForegroundColor Green
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend is NOT running!" -ForegroundColor Red
    Write-Host "   Please start the backend first:" -ForegroundColor Yellow
    Write-Host "   cd 'c:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate\backend'" -ForegroundColor Gray
    Write-Host "   `$env:DATABASE_URL='postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat'" -ForegroundColor Gray
    Write-Host "   python main.py" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "Test 2: Checking LLM providers..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/chat/providers" -UseBasicParsing
    $providers = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ LLM Providers Response:" -ForegroundColor Green
    Write-Host "   Available: $($providers.providers -join ', ')" -ForegroundColor Gray
    
    if ($providers.health.ollama) {
        $ollamaStatus = if ($providers.health.ollama.available) { "✅ Available" } else { "❌ Not Available" }
        Write-Host "   Ollama: $ollamaStatus" -ForegroundColor Gray
    }
    
    if ($providers.health.gemini) {
        $geminiStatus = if ($providers.health.gemini.available) { "✅ Available" } else { "❌ Not Available" }
        Write-Host "   Gemini: $geminiStatus" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to check providers: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Test 3: Testing Gemini chat..." -ForegroundColor Yellow
try {
    $body = @{
        message = "What is ocean salinity?"
        provider = "gemini"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    
    if ($result.success) {
        Write-Host "✅ Gemini is working!" -ForegroundColor Green
        Write-Host "   Response: $($result.response.Substring(0, [Math]::Min(100, $result.response.Length)))..." -ForegroundColor Gray
        Write-Host "   Source: $($result.source)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Gemini test failed: $($result.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Chat test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Backend Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Visit http://localhost:8000/docs to see all API endpoints" -ForegroundColor Gray
Write-Host "2. Test the chat at http://localhost:8000/api/chat" -ForegroundColor Gray
Write-Host "3. Check ARGO data at http://localhost:8000/api/v1/argo/stats/summary" -ForegroundColor Gray
Write-Host ""
