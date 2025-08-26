# PowerShell test script for CumRoad SOAP API
param(
    [string]$ServiceUrl = "http://localhost:8080"
)

Write-Host "CumRoad SOAP API Test Suite" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""

$TestsPassed = 0
$TestsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers,
        [string]$Body = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        if ($Body) {
            $Response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -Body $Body -ErrorAction Stop
        } else {
            $Response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $Headers -ErrorAction Stop
        }
        
        Write-Host "✅ PASS: $Name" -ForegroundColor Green
        $script:TestsPassed++
        return $Response
    }
    catch {
        Write-Host "❌ FAIL: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $script:TestsFailed++
        return $null
    }
}

function Test-SOAPEndpoint {
    param(
        [string]$Name,
        [string]$SOAPAction,
        [string]$Body
    )
    
    $Headers = @{
        'Content-Type' = 'text/xml; charset=utf-8'
        'SOAPAction' = $SOAPAction
    }
    
    return Test-Endpoint -Name $Name -Method "POST" -Url "$ServiceUrl/soap" -Headers $Headers -Body $Body
}

# Test 1: Health Check
Write-Host "1. Health Check Test" -ForegroundColor Cyan
Test-Endpoint -Name "Health endpoint" -Method "GET" -Url "$ServiceUrl/health" -Headers @{}

# Test 2: WSDL Availability
Write-Host "`n2. WSDL Availability Test" -ForegroundColor Cyan
Test-Endpoint -Name "WSDL endpoint" -Method "GET" -Url "$ServiceUrl/wsdl" -Headers @{}

# Test 3: SOAP Operations
Write-Host "`n3. SOAP Operations Tests" -ForegroundColor Cyan

# Test GetAllProducts (should return empty list initially)
$GetProductsSOAP = @'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:GetAllProductsRequest/>
    </soap:Body>
</soap:Envelope>
'@

Test-SOAPEndpoint -Name "GetAllProducts" -SOAPAction "http://cumroad.api.soap/service/GetAllProducts" -Body $GetProductsSOAP

# Test CreateUser
$CreateUserSOAP = @'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:CreateUserRequest>
            <types:user>
                <types:email>testuser@example.com</types:email>
                <types:password>testpass123</types:password>
                <types:name>Test User</types:name>
            </types:user>
        </types:CreateUserRequest>
    </soap:Body>
</soap:Envelope>
'@

$UserResponse = Test-SOAPEndpoint -Name "CreateUser" -SOAPAction "http://cumroad.api.soap/service/CreateUser" -Body $CreateUserSOAP

# Test Login
$LoginSOAP = @'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>testuser@example.com</types:email>
                <types:password>testpass123</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>
'@

$LoginResponse = Test-SOAPEndpoint -Name "Login" -SOAPAction "http://cumroad.api.soap/service/Login" -Body $LoginSOAP

# Test GetAllUsers
$GetUsersSOAP = @'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:GetAllUsersRequest/>
    </soap:Body>
</soap:Envelope>
'@

Test-SOAPEndpoint -Name "GetAllUsers" -SOAPAction "http://cumroad.api.soap/service/GetAllUsers" -Body $GetUsersSOAP

# Results Summary
Write-Host "`n" + "="*50 -ForegroundColor Green
Write-Host "TEST RESULTS SUMMARY" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host "Tests Passed: $TestsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -eq 0) { "Green" } else { "Red" })
Write-Host "Total Tests: $($TestsPassed + $TestsFailed)" -ForegroundColor White

if ($TestsFailed -eq 0) {
    Write-Host "`n🎉 All tests passed! SOAP API is working correctly." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Some tests failed. Please check the service." -ForegroundColor Red
    exit 1
}
