#!/bin/bash

# CumRoad SOAP Service Test Script
echo "Starting CumRoad SOAP Service Tests..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    echo "Waiting for service to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo "Service is ready!"
            return 0
        fi
        echo "Waiting... ($i/30)"
        sleep 2
    done
    echo "Service failed to start within timeout"
    return 1
}

# Function to run WSDL validation tests
test_wsdl_validation() {
    echo ""
    echo "=== WSDL VALIDATION TESTS ==="
    
    # Test 1: WSDL is accessible
    echo "Test 1: Checking if WSDL is accessible..."
    if curl -s -f http://localhost:8080/wsdl > /dev/null; then
        echo "✓ PASS: WSDL is accessible"
    else
        echo "✗ FAIL: WSDL is not accessible"
        return 1
    fi
    
    # Test 2: WSDL is valid XML
    echo "Test 2: Validating WSDL XML structure..."
    if curl -s http://localhost:8080/wsdl | xmllint --noout - 2>/dev/null; then
        echo "✓ PASS: WSDL is valid XML"
    else
        echo "✗ FAIL: WSDL is not valid XML"
        return 1
    fi
    
    # Test 3: WSDL contains required elements
    echo "Test 3: Checking WSDL content..."
    wsdl_content=$(curl -s http://localhost:8080/wsdl)
    
    if echo "$wsdl_content" | grep -q "definitions"; then
        echo "✓ PASS: WSDL contains definitions element"
    else
        echo "✗ FAIL: WSDL missing definitions element"
        return 1
    fi
    
    if echo "$wsdl_content" | grep -q "portType"; then
        echo "✓ PASS: WSDL contains portType element"
    else
        echo "✗ FAIL: WSDL missing portType element"
        return 1
    fi
    
    if echo "$wsdl_content" | grep -q "binding"; then
        echo "✓ PASS: WSDL contains binding element"
    else
        echo "✗ FAIL: WSDL missing binding element"
        return 1
    fi
    
    if echo "$wsdl_content" | grep -q "service"; then
        echo "✓ PASS: WSDL contains service element"
    else
        echo "✗ FAIL: WSDL missing service element"
        return 1
    fi
    
    return 0
}

# Function to test SOAP operations
test_soap_operations() {
    echo ""
    echo "=== SOAP OPERATIONS TESTS ==="
    
    # Test user creation
    echo "Test 1: Creating a test user..."
    create_user_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/CreateUser" \
        -d '<?xml version="1.0" encoding="utf-8"?>
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
</soap:Envelope>')
    
    if echo "$create_user_response" | grep -q "CreateUserResponse"; then
        echo "✓ PASS: User creation successful"
        # Extract user ID for further tests
        user_id=$(echo "$create_user_response" | grep -o '<types:id>[^<]*' | sed 's/<types:id>//')
        echo "  Created user ID: $user_id"
    else
        echo "✗ FAIL: User creation failed"
        echo "Response: $create_user_response"
        return 1
    fi
    
    # Test user login
    echo "Test 2: Testing user login..."
    login_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/Login" \
        -d '<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>test@example.com</types:email>
                <types:password>password123</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>')
    
    if echo "$login_response" | grep -q "LoginResponse"; then
        echo "✓ PASS: User login successful"
        # Extract token for further tests
        token=$(echo "$login_response" | grep -o '<types:token>[^<]*' | sed 's/<types:token>//')
        echo "  Received token: ${token:0:20}..."
    else
        echo "✗ FAIL: User login failed"
        echo "Response: $login_response"
        return 1
    fi
    
    # Test get all users
    echo "Test 3: Getting all users..."
    get_users_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/GetAllUsers" \
        -d '<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllUsersRequest/>
    </soap:Body>
</soap:Envelope>')
    
    if echo "$get_users_response" | grep -q "GetAllUsersResponse"; then
        echo "✓ PASS: Get all users successful"
    else
        echo "✗ FAIL: Get all users failed"
        echo "Response: $get_users_response"
        return 1
    fi
    
    # Test create product
    echo "Test 4: Creating a test product..."
    create_product_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/CreateProduct" \
        -d "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:tns=\"http://cumroad.api.soap/service\" xmlns:types=\"http://cumroad.api.soap/types\">
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
</soap:Envelope>")
    
    if echo "$create_product_response" | grep -q "CreateProductResponse"; then
        echo "✓ PASS: Product creation successful"
        product_id=$(echo "$create_product_response" | grep -o '<types:id>[^<]*' | tail -1 | sed 's/<types:id>//')
        echo "  Created product ID: $product_id"
    else
        echo "✗ FAIL: Product creation failed"
        echo "Response: $create_product_response"
        return 1
    fi
    
    # Test get all products
    echo "Test 5: Getting all products..."
    get_products_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/GetAllProducts" \
        -d '<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllProductsRequest/>
    </soap:Body>
</soap:Envelope>')
    
    if echo "$get_products_response" | grep -q "GetAllProductsResponse"; then
        echo "✓ PASS: Get all products successful"
    else
        echo "✗ FAIL: Get all products failed"
        echo "Response: $get_products_response"
        return 1
    fi
    
    return 0
}

# Function to test error handling
test_error_handling() {
    echo ""
    echo "=== ERROR HANDLING TESTS ==="
    
    # Test invalid user creation
    echo "Test 1: Testing invalid user creation..."
    invalid_user_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/CreateUser" \
        -d '<?xml version="1.0" encoding="utf-8"?>
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
</soap:Envelope>')
    
    if echo "$invalid_user_response" | grep -q "soap:Fault\|Fault"; then
        echo "✓ PASS: Invalid user creation properly returns fault"
    else
        echo "✗ FAIL: Invalid user creation should return fault"
        echo "Response: $invalid_user_response"
        return 1
    fi
    
    # Test invalid login
    echo "Test 2: Testing invalid login..."
    invalid_login_response=$(curl -s -X POST http://localhost:8080/soap \
        -H "Content-Type: text/xml; charset=utf-8" \
        -H "SOAPAction: http://cumroad.api.soap/service/Login" \
        -d '<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://cumroad.api.soap/service" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:LoginRequest>
            <types:credentials>
                <types:email>nonexistent@example.com</types:email>
                <types:password>wrongpassword</types:password>
            </types:credentials>
        </types:LoginRequest>
    </soap:Body>
</soap:Envelope>')
    
    if echo "$invalid_login_response" | grep -q "soap:Fault\|Fault"; then
        echo "✓ PASS: Invalid login properly returns fault"
    else
        echo "✗ FAIL: Invalid login should return fault"
        echo "Response: $invalid_login_response"
        return 1
    fi
    
    return 0
}

# Function to run automated client test
test_python_client() {
    echo ""
    echo "=== PYTHON CLIENT TESTS ==="
    
    # Check if Python is available
    if ! command_exists python3; then
        echo "✗ SKIP: Python 3 not available for client tests"
        return 0
    fi
    
    # Create client virtual environment if needed
    if [ ! -d "client_venv" ]; then
        echo "Creating client virtual environment..."
        python3 -m venv client_venv
    fi
    
    # Activate virtual environment and install dependencies
    source client_venv/bin/activate
    pip install -q -r client/requirements.txt
    
    # Run client test
    echo "Running Python client test..."
    if python3 client/example.py > client_test.log 2>&1; then
        echo "✓ PASS: Python client test successful"
    else
        echo "✗ FAIL: Python client test failed"
        echo "Client test log:"
        cat client_test.log
        deactivate
        return 1
    fi
    
    deactivate
    return 0
}

# Main test execution
main() {
    echo "CumRoad SOAP Service Test Suite"
    echo "==============================="
    
    # Check prerequisites
    if ! command_exists curl; then
        echo "Error: curl is required for tests"
        exit 1
    fi
    
    if ! command_exists xmllint; then
        echo "Warning: xmllint not available, skipping XML validation"
    fi
    
    # Start service in background if not running
    service_running=false
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "Service is already running"
        service_running=true
    else
        echo "Starting service for tests..."
        if [ -f "scripts/run.sh" ]; then
            bash scripts/run.sh > service.log 2>&1 &
            service_pid=$!
        else
            python3 src/soap_service.py > service.log 2>&1 &
            service_pid=$!
        fi
        
        # Wait for service to start
        if wait_for_service; then
            service_running=true
        else
            echo "Failed to start service"
            exit 1
        fi
    fi
    
    # Run tests
    test_failed=false
    
    if ! test_wsdl_validation; then
        test_failed=true
    fi
    
    if ! test_soap_operations; then
        test_failed=true
    fi
    
    if ! test_error_handling; then
        test_failed=true
    fi
    
    if ! test_python_client; then
        test_failed=true
    fi
    
    # Stop service if we started it
    if [ ! "$service_running" = true ] && [ ! -z "$service_pid" ]; then
        echo ""
        echo "Stopping test service..."
        kill $service_pid 2>/dev/null || true
        wait $service_pid 2>/dev/null || true
    fi
    
    # Report results
    echo ""
    echo "==============================="
    if [ "$test_failed" = true ]; then
        echo "❌ SOME TESTS FAILED"
        echo "Check the output above for details"
        exit 1
    else
        echo "✅ ALL TESTS PASSED"
        echo "SOAP service is working correctly!"
        exit 0
    fi
}

# Run main function
main "$@"
