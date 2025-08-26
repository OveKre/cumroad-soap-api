#!/bin/bash

# CumRoad SOAP Service Run Script
echo "Setting up CumRoad SOAP Service..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=src/soap_service.py
export FLASK_ENV=development
export JWT_SECRET=your-secret-key-change-this-in-production

# Run the service
echo "Starting CumRoad SOAP Service..."
echo "WSDL will be available at: http://localhost:8080/wsdl"
echo "SOAP endpoint: http://localhost:8080/soap"
echo "Health check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the service"

cd "$(dirname "$0")"
python3 src/soap_service.py
