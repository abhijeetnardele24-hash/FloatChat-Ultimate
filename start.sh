#!/bin/bash

# FloatChat Ultimate - Complete Startup Script

echo "🌊 Starting FloatChat Ultimate..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Start all services
echo "🐳 Starting Docker services (PostgreSQL, Redis, Ollama, Backend)..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if Ollama model is downloaded
echo "🤖 Checking Ollama model..."
docker exec floatchat-ollama ollama list | grep llama2 > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "📥 Downloading Llama2 model (this may take a few minutes)..."
    docker exec floatchat-ollama ollama pull llama2
fi

echo "✅ Ollama model ready"

# Run data ingestion (optional)
read -p "Do you want to ingest ARGO data now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Starting ARGO data ingestion..."
    docker exec floatchat-backend python data_ingestion/argo_ingestion.py
fi

echo ""
echo "✅ FloatChat Ultimate is running!"
echo ""
echo "📍 Access Points:"
echo "   - Frontend:      http://localhost:3000"
echo "   - Backend API:   http://localhost:8000"
echo "   - API Docs:      http://localhost:8000/docs"
echo "   - PostgreSQL:    localhost:5432"
echo "   - Redis:         localhost:6379"
echo "   - Ollama:        http://localhost:11434"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f backend"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
