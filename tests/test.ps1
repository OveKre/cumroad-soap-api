# CumRoad SOAP Service Test Script for Windows
param(
    [switch]$SkipClientTests = $false
)

Write-Host "CumRoad SOAP Service Test Suite" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Function to wait for service to be ready
function Wait-ForService {
    Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 2
            if ($response.status -eq "ok") {
                Write-Host "Service is ready!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
        Write-Host "Waiting... ($i/30)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
    Write-Host "Service failed to start within timeout" -ForegroundColor Red
    return $false
}

# Function to test WSDL validation
function Test-WsdlValidation {
    Write-Host ""
    Write-Host "=== WSDL VALIDATION TESTS ===" -ForegroundColor Cyan
    
    $success = $true
    
    # Test 1: WSDL is accessible
    Write-Host "Test 1: Checking if WSDL is accessible..." -ForegroundColor Yellow
    try {
        $wsdl = Invoke-RestMethod -Uri "http://localhost:8080/wsdl" -TimeoutSec 10
        Write-Host "✓ PASS: WSDL is accessible" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ FAIL: WSDL is not accessible" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        $success = $false
    }
    
    # Test 2: WSDL contains required elements
    if ($success) {
        Write-Host "Test 2: Checking WSDL content..." -ForegroundColor Yellow
        try {
            $wsdlContent = Invoke-RestMethod -Uri "http://localhost:8080/wsdl" -TimeoutSec 10
            
            if ($wsdlContent -match "definitions") {
                Write-Host "✓ PASS: WSDL contains definitions element" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: WSDL missing definitions element" -ForegroundColor Red
                $success = $false
            }
            
            if ($wsdlContent -match "portType") {
                Write-Host "✓ PASS: WSDL contains portType element" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: WSDL missing portType element" -ForegroundColor Red
                $success = $false
            }
            
            if ($wsdlContent -match "binding") {
                Write-Host "✓ PASS: WSDL contains binding element" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: WSDL missing binding element" -ForegroundColor Red
                $success = $false
            }
            
            if ($wsdlContent -match "service") {
                Write-Host "✓ PASS: WSDL contains service element" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: WSDL missing service element" -ForegroundColor Red
                $success = $false
            }
        }
        catch {
            Write-Host "✗ FAIL: Error checking WSDL content" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    return $success
}

# Function to invoke SOAP operation
function Invoke-SoapOperation {
    param(
        [string]$SoapAction,
        [string]$SoapBody
    )
    
    $headers = @{
        "Content-Type" = "text/xml; charset=utf-8"
        "SOAPAction" = $SoapAction
    }
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/soap" -Method POST -Headers $headers -Body $SoapBody -TimeoutSec 10
        return $response
    }
    catch {
        return $_.Exception.Response
    }
}

# Function to test SOAP operations
function Test-SoapOperations {
    Write-Host ""
    Write-Host "=== SOAP OPERATIONS TESTS ===" -ForegroundColor Cyan
    
    $success = $true
    $userId = $null
    $token = $null
    $productId = $null
    
    # Test user creation
    Write-Host "Test 1: Creating a test user..." -ForegroundColor Yellow
    $createUserSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateUserRequest>
            <types:user>
                <types:email>test@example.com</types:email>
                <types:password>password123</types:password>
                <types:name>Test User</types:name>
            </types:user>
        </types:CreateUserRequest>
    </soap:Body>
</soap:Envelope>
'@
    
    try {
        $createUserResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/CreateUser" -SoapBody $createUserSoap
        if ($createUserResponse -match "CreateUserResponse") {
            Write-Host "✓ PASS: User creation successful" -ForegroundColor Green
            # Extract user ID
            if ($createUserResponse -match "<types:id>(\d+)</types:id>") {
                $userId = $Matches[1]
                Write-Host "  Created user ID: $userId" -ForegroundColor Gray
            }
        } else {
            Write-Host "✗ FAIL: User creation failed" -ForegroundColor Red
            $success = $false
        }
    }
    catch {
        Write-Host "✗ FAIL: User creation failed with error" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        $success = $false
    }
    
    # Test user login
    if ($success) {
        Write-Host "Test 2: Testing user login..." -ForegroundColor Yellow
        $loginSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>test@example.com</types:email>
                <types:password>password123</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>
'@
        
        try {
            $loginResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/Login" -SoapBody $loginSoap
            if ($loginResponse -match "LoginResponse") {
                Write-Host "✓ PASS: User login successful" -ForegroundColor Green
                # Extract token
                if ($loginResponse -match "<types:token>([^<]+)</types:token>") {
                    $token = $Matches[1]
                    Write-Host "  Received token: $($token.Substring(0, [Math]::Min(20, $token.Length)))..." -ForegroundColor Gray
                }
            } else {
                Write-Host "✗ FAIL: User login failed" -ForegroundColor Red
                $success = $false
            }
        }
        catch {
            Write-Host "✗ FAIL: User login failed with error" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    # Test get all users
    if ($success) {
        Write-Host "Test 3: Getting all users..." -ForegroundColor Yellow
        $getUsersSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllUsersRequest/>
    </soap:Body>
</soap:Envelope>
'@
        
        try {
            $getUsersResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/GetAllUsers" -SoapBody $getUsersSoap
            if ($getUsersResponse -match "GetAllUsersResponse") {
                Write-Host "✓ PASS: Get all users successful" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: Get all users failed" -ForegroundColor Red
                $success = $false
            }
        }
        catch {
            Write-Host "✗ FAIL: Get all users failed with error" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    # Test create product
    if ($success -and $token) {
        Write-Host "Test 4: Creating a test product..." -ForegroundColor Yellow
        $createProductSoap = @"
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateProductRequest>
            <types:product>
                <types:name>Test Product</types:name>
                <types:description>Test Description</types:description>
                <types:price>19.99</types:price>
                <types:image_url>https://example.com/test.jpg</types:image_url>
            </types:product>
            <types:token>$token</types:token>
        </types:CreateProductRequest>
    </soap:Body>
</soap:Envelope>
"@
        
        try {
            $createProductResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/CreateProduct" -SoapBody $createProductSoap
            if ($createProductResponse -match "CreateProductResponse") {
                Write-Host "✓ PASS: Product creation successful" -ForegroundColor Green
                # Extract product ID
                if ($createProductResponse -match "<types:id>(\d+)</types:id>") {
                    $productId = $Matches[1]
                    Write-Host "  Created product ID: $productId" -ForegroundColor Gray
                }
            } else {
                Write-Host "✗ FAIL: Product creation failed" -ForegroundColor Red
                $success = $false
            }
        }
        catch {
            Write-Host "✗ FAIL: Product creation failed with error" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    # Test get all products
    if ($success) {
        Write-Host "Test 5: Getting all products..." -ForegroundColor Yellow
        $getProductsSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllProductsRequest/>
    </soap:Body>
</soap:Envelope>
'@
        
        try {
            $getProductsResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/GetAllProducts" -SoapBody $getProductsSoap
            if ($getProductsResponse -match "GetAllProductsResponse") {
                Write-Host "✓ PASS: Get all products successful" -ForegroundColor Green
            } else {
                Write-Host "✗ FAIL: Get all products failed" -ForegroundColor Red
                $success = $false
            }
        }
        catch {
            Write-Host "✗ FAIL: Get all products failed with error" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    return @{
        Success = $success
        UserId = $userId
        Token = $token
        ProductId = $productId
    }
}

# Function to test error handling
function Test-ErrorHandling {
    Write-Host ""
    Write-Host "=== ERROR HANDLING TESTS ===" -ForegroundColor Cyan
    
    $success = $true
    
    # Test invalid user creation
    Write-Host "Test 1: Testing invalid user creation..." -ForegroundColor Yellow
    $invalidUserSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateUserRequest>
            <types:user>
                <types:email>invalid-email</types:email>
                <types:password>123</types:password>
                <types:name>Test User</types:name>
            </types:user>
        </types:CreateUserRequest>
    </soap:Body>
</soap:Envelope>
'@
    
    try {
        $invalidUserResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/CreateUser" -SoapBody $invalidUserSoap
        if ($invalidUserResponse -match "soap:Fault|Fault") {
            Write-Host "✓ PASS: Invalid user creation properly returns fault" -ForegroundColor Green
        } else {
            Write-Host "✗ FAIL: Invalid user creation should return fault" -ForegroundColor Red
            $success = $false
        }
    }
    catch {
        Write-Host "✓ PASS: Invalid user creation properly throws error" -ForegroundColor Green
    }
    
    # Test invalid login
    Write-Host "Test 2: Testing invalid login..." -ForegroundColor Yellow
    $invalidLoginSoap = @'
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>nonexistent@example.com</types:email>
                <types:password>wrongpassword</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>
'@
    
    try {
        $invalidLoginResponse = Invoke-SoapOperation -SoapAction "http://cumroad.api.soap/service/Login" -SoapBody $invalidLoginSoap
        if ($invalidLoginResponse -match "soap:Fault|Fault") {
            Write-Host "✓ PASS: Invalid login properly returns fault" -ForegroundColor Green
        } else {
            Write-Host "✗ FAIL: Invalid login should return fault" -ForegroundColor Red
            $success = $false
        }
    }
    catch {
        Write-Host "✓ PASS: Invalid login properly throws error" -ForegroundColor Green
    }
    
    return $success
}

# Function to test Python client
function Test-PythonClient {
    Write-Host ""
    Write-Host "=== PYTHON CLIENT TESTS ===" -ForegroundColor Cyan
    
    if ($SkipClientTests) {
        Write-Host "✗ SKIP: Python client tests skipped by user request" -ForegroundColor Yellow
        return $true
    }
    
    # Check if Python is available
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "✗ SKIP: Python not available for client tests" -ForegroundColor Yellow
        return $true
    }
    
    try {
        # Create client virtual environment if needed
        if (-not (Test-Path "client_venv")) {
            Write-Host "Creating client virtual environment..." -ForegroundColor Yellow
            python -m venv client_venv
        }
        
        # Activate virtual environment and install dependencies
        & "client_venv\Scripts\Activate.ps1"
        pip install -q -r client/requirements.txt
        
        # Run client test
        Write-Host "Running Python client test..." -ForegroundColor Yellow
        $clientOutput = python client/example.py 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ PASS: Python client test successful" -ForegroundColor Green
        } else {
            Write-Host "✗ FAIL: Python client test failed" -ForegroundColor Red
            Write-Host "Client output:" -ForegroundColor Red
            Write-Host $clientOutput -ForegroundColor Red
            deactivate
            return $false
        }
        
        deactivate
        return $true
    }
    catch {
        Write-Host "✗ FAIL: Python client test failed with error" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main test execution
function Main {
    # Check if service is already running
    $serviceRunning = $false
    $serviceProcess = $null
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 2
        if ($response.status -eq "ok") {
            Write-Host "Service is already running" -ForegroundColor Green
            $serviceRunning = $true
        }
    }
    catch {
        Write-Host "Starting service for tests..." -ForegroundColor Yellow
        
        # Start service in background
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $projectRoot = Split-Path -Parent $scriptDir
        Set-Location $projectRoot
        
        if (Test-Path "scripts\run.ps1") {
            $serviceProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-File scripts\run.ps1" -NoNewWindow -PassThru -RedirectStandardOutput "service.log" -RedirectStandardError "service_error.log"
        } else {
            $serviceProcess = Start-Process -FilePath "python" -ArgumentList "src\soap_service.py" -NoNewWindow -PassThru -RedirectStandardOutput "service.log" -RedirectStandardError "service_error.log"
        }
        
        # Wait for service to start
        if (Wait-ForService) {
            $serviceRunning = $true
        } else {
            Write-Host "Failed to start service" -ForegroundColor Red
            if ($serviceProcess) { $serviceProcess.Kill() }
            exit 1
        }
    }
    
    # Run tests
    $testFailed = $false
    
    if (-not (Test-WsdlValidation)) {
        $testFailed = $true
    }
    
    $soapResults = Test-SoapOperations
    if (-not $soapResults.Success) {
        $testFailed = $true
    }
    
    if (-not (Test-ErrorHandling)) {
        $testFailed = $true
    }
    
    if (-not (Test-PythonClient)) {
        $testFailed = $true
    }
    
    # Stop service if we started it
    if (-not $serviceRunning -and $serviceProcess) {
        Write-Host ""
        Write-Host "Stopping test service..." -ForegroundColor Yellow
        try {
            $serviceProcess.Kill()
            $serviceProcess.WaitForExit(5000)
        }
        catch {
            Write-Host "Warning: Could not stop service process" -ForegroundColor Yellow
        }
    }
    
    # Report results
    Write-Host ""
    Write-Host "===============================" -ForegroundColor Green
    if ($testFailed) {
        Write-Host "❌ SOME TESTS FAILED" -ForegroundColor Red
        Write-Host "Check the output above for details" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "✅ ALL TESTS PASSED" -ForegroundColor Green
        Write-Host "SOAP service is working correctly!" -ForegroundColor Green
        exit 0
    }
}

# Run main function
Main
