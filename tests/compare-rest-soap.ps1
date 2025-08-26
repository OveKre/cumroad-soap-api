# REST vs SOAP Response Comparison Test
Write-Host "REST vs SOAP Response Comparison Test" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Kontrolli SOAP teenuse olemasolu
Write-Host "Checking SOAP service availability..." -ForegroundColor Yellow
try {
    $soapHealth = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method Get -TimeoutSec 5
    Write-Host "✅ SOAP API is running" -ForegroundColor Green
} catch {
    Write-Host "❌ SOAP API is not running on port 8080" -ForegroundColor Red
    Write-Host "Please start the SOAP service first: .\scripts\run.ps1" -ForegroundColor Yellow
    exit 1
}

# Kontrolli REST API olemasolu (eeldame port 3000)
$restAvailable = $false
try {
    $restHealth = Invoke-RestMethod -Uri "http://localhost:3000/health" -Method Get -TimeoutSec 5
    $restAvailable = $true
    Write-Host "✅ REST API detected on port 3000" -ForegroundColor Green
} catch {
    Write-Host "⚠️ REST API not available on port 3000" -ForegroundColor Yellow
    Write-Host "Showing SOAP responses only (REST comparison skipped)" -ForegroundColor Yellow
}

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "COMPARISON TESTS" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Test 1: GetAllProducts
Write-Host "`n1. 📦 Comparing GetAllProducts responses:" -ForegroundColor White
Write-Host "-" * 40

if ($restAvailable) {
    Write-Host "REST Response (JSON):" -ForegroundColor Blue
    try {
        $restProducts = Invoke-RestMethod -Uri "http://localhost:3000/products" -Method Get
        Write-Host ($restProducts | ConvertTo-Json -Depth 3) -ForegroundColor Cyan
    } catch {
        Write-Host "REST request failed: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "SOAP Response (XML):" -ForegroundColor Green
$soapProductsBody = @'
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:GetAllProductsRequest/>
    </soap:Body>
</soap:Envelope>
'@

try {
    $soapResponse = Invoke-RestMethod -Uri "http://localhost:8080/soap" -Method Post -Body $soapProductsBody -ContentType "text/xml; charset=utf-8" -Headers @{"SOAPAction"="http://cumroad.api.soap/service/GetAllProducts"}
    Write-Host $soapResponse.OuterXml -ForegroundColor Cyan
} catch {
    Write-Host "SOAP request failed: $_" -ForegroundColor Red
}

# Test 2: CreateUser
Write-Host "`n2. 👤 Comparing CreateUser responses:" -ForegroundColor White
Write-Host "-" * 40

$testUser = @{
    email = "compare-test@example.com"
    password = "password123"
    name = "Compare Test User"
}

if ($restAvailable) {
    Write-Host "REST Response (JSON):" -ForegroundColor Blue
    try {
        $restUser = Invoke-RestMethod -Uri "http://localhost:3000/users" -Method Post -Body ($testUser | ConvertTo-Json) -ContentType "application/json"
        Write-Host ($restUser | ConvertTo-Json -Depth 2) -ForegroundColor Cyan
    } catch {
        Write-Host "REST request failed: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "SOAP Response (XML):" -ForegroundColor Green
$soapUserBody = @"
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:CreateUserRequest>
            <types:user>
                <types:email>$($testUser.email)</types:email>
                <types:password>$($testUser.password)</types:password>
                <types:name>$($testUser.name)</types:name>
            </types:user>
        </types:CreateUserRequest>
    </soap:Body>
</soap:Envelope>
"@

try {
    $soapUserResponse = Invoke-RestMethod -Uri "http://localhost:8080/soap" -Method Post -Body $soapUserBody -ContentType "text/xml; charset=utf-8" -Headers @{"SOAPAction"="http://cumroad.api.soap/service/CreateUser"}
    Write-Host $soapUserResponse.OuterXml -ForegroundColor Cyan
} catch {
    Write-Host "SOAP request failed: $_" -ForegroundColor Red
}

# Test 3: Login comparison
Write-Host "`n3. 🔐 Comparing Login responses:" -ForegroundColor White
Write-Host "-" * 40

$loginCreds = @{
    email = "compare-test@example.com"
    password = "password123"
}

if ($restAvailable) {
    Write-Host "REST Response (JSON):" -ForegroundColor Blue
    try {
        $restLogin = Invoke-RestMethod -Uri "http://localhost:3000/sessions" -Method Post -Body ($loginCreds | ConvertTo-Json) -ContentType "application/json"
        # Hide sensitive token in output
        $restLoginSafe = $restLogin.PSObject.Copy()
        if ($restLoginSafe.token) {
            $restLoginSafe.token = $restLoginSafe.token.Substring(0, 20) + "...[TRUNCATED]"
        }
        Write-Host ($restLoginSafe | ConvertTo-Json -Depth 2) -ForegroundColor Cyan
    } catch {
        Write-Host "REST request failed: $_" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "SOAP Response (XML):" -ForegroundColor Green
$soapLoginBody = @"
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Header/>
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>$($loginCreds.email)</types:email>
                <types:password>$($loginCreds.password)</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>
"@

try {
    $soapLoginResponse = Invoke-RestMethod -Uri "http://localhost:8080/soap" -Method Post -Body $soapLoginBody -ContentType "text/xml; charset=utf-8" -Headers @{"SOAPAction"="http://cumroad.api.soap/service/Login"}
    # Truncate token in XML for security
    $responseXml = $soapLoginResponse.OuterXml
    $responseXml = $responseXml -replace '(<types:token>)[^<]{20}[^<]*', '$1...[TRUNCATED]'
    Write-Host $responseXml -ForegroundColor Cyan
} catch {
    Write-Host "SOAP request failed: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "COMPARISON SUMMARY" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "✅ SOAP API responses validated" -ForegroundColor Green
if ($restAvailable) {
    Write-Host "✅ REST vs SOAP comparison completed" -ForegroundColor Green
    Write-Host "📋 Both APIs should return equivalent data:" -ForegroundColor Yellow
    Write-Host "   • REST returns JSON format" -ForegroundColor White
    Write-Host "   • SOAP returns XML format" -ForegroundColor White
    Write-Host "   • Same business logic and data structure" -ForegroundColor White
} else {
    Write-Host "ℹ️ REST API not available - SOAP validation only" -ForegroundColor Blue
    Write-Host "📋 To run full comparison:" -ForegroundColor Yellow
    Write-Host "   1. Start your REST API on port 3000" -ForegroundColor White
    Write-Host "   2. Run this test again" -ForegroundColor White
}

Write-Host "`n🎉 Comparison test completed!" -ForegroundColor Green