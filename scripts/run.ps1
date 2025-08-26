# CumRoad SOAP Service Run Script for Windows
Write-Host "Setting up CumRoad SOAP Service..." -ForegroundColor Green

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Set environment variables
$env:FLASK_APP = "src/soap_service.py"
$env:FLASK_ENV = "development"
$env:JWT_SECRET = "your-secret-key-change-this-in-production"

# Run the service
Write-Host ""
Write-Host "Starting CumRoad SOAP Service..." -ForegroundColor Green
Write-Host "WSDL will be available at: http://localhost:8080/wsdl" -ForegroundColor Cyan
Write-Host "SOAP endpoint: http://localhost:8080/soap" -ForegroundColor Cyan
Write-Host "Health check: http://localhost:8080/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

python src/simple_soap_service.py
