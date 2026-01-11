#!/bin/bash

# Karate Task Tracker Setup Script

echo "🥋 Karate Task Tracker Setup"
echo "=============================="
echo ""

# Create data directory
mkdir -p data
echo "✅ Created data directory"

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    
    # Check if Docker Compose is installed
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose is installed"
        echo ""
        echo "Building and starting the application..."
        echo ""
        docker-compose down 2>/dev/null
        docker-compose up --build -d
        echo ""
        echo "✅ Application is running!"
        echo "📱 Access it at: http://localhost:8000"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
    else
        echo "❌ Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    fi
else
    echo "❌ Docker is not installed"
    echo ""
    echo "Installing manually..."
    echo ""
    
    # Check if Python is installed
    if command -v python3 &> /dev/null; then
        echo "✅ Python is installed"
        echo ""
        echo "Creating virtual environment..."
        python3 -m venv venv
        
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        echo "Installing dependencies..."
        pip install -r requirements.txt
        
        echo ""
        echo "✅ Setup complete!"
        echo ""
        echo "To start the application:"
        echo "  1. source venv/bin/activate"
        echo "  2. python main.py"
        echo ""
        echo "Then access it at: http://localhost:8000"
    else
        echo "❌ Python 3 is not installed"
        echo "Please install Python 3.8 or higher"
    fi
fi
