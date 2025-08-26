# CumRoad SOAP API

A SOAP web service that replicates the functionality of a REST API for an e-commerce platform. This project demonstrates how to convert REST endpoints to SOAP operations while maintaining equivalent business logic and error handling.

## Project Overview

This SOAP service provides the same functionality as the original REST API, including:
- User management (create, read, update, delete)
- Authentication and session management
- Product management
- Order management
- Comprehensive error handling with SOAP faults

## Features

- ✅ Complete WSDL definition with XSD schemas
- ✅ All REST endpoints converted to SOAP operations
- ✅ JWT-based authentication
- ✅ SQLite database for data persistence
- ✅ Comprehensive error handling with SOAP faults
- ✅ Docker support
- ✅ Automated testing suite
- ✅ Python client example

## Project Structure

```
/project-root
 ├── wsdl/              # WSDL and XSD files
 │   └── cumroad-api.wsdl
 ├── src/               # Source code
 │   ├── soap_service.py         # Original Spyne implementation
 │   └── simple_soap_service.py  # Working Flask SOAP service
 ├── scripts/           # Build and run scripts
 │   ├── run.sh         # Linux/Mac run script
 │   ├── run.ps1        # Windows PowerShell script
 │   └── test.ps1       # Basic SOAP service tests
 ├── client/            # Client examples
 │   ├── example.py     # Python client demonstration
 │   └── requirements.txt
 ├── tests/             # Advanced testing and comparison
 │   ├── test.sh                # Linux/Mac test script
 │   ├── compare-rest-soap.ps1  # REST vs SOAP comparison test
 │   ├── compare-analysis.py    # Python response analysis tool
 │   └── response-analysis.md   # Detailed comparison documentation
 ├── Dockerfile         # Docker container configuration
 ├── docker-compose.yml # Docker Compose configuration
 ├── requirements.txt   # Python dependencies
 └── README.md          # This file
```

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

### Optional:
- Docker and Docker Compose (for containerized deployment)
- curl (for testing)
- xmllint (for WSDL validation)

## Quick Start

### Option 1: Using Scripts (Recommended)

#### Windows (PowerShell):
```powershell
.\scripts\run.ps1
```

#### Linux/Mac:
```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

### Option 2: Manual Setup

1. **Create virtual environment:**
```bash
python -m venv venv
```

2. **Activate virtual environment:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the service:**
```bash
python src/soap_service.py
```

### Option 3: Using Docker

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Or build manually:**
```bash
docker build -t cumroad-soap .
docker run -p 8080:8080 cumroad-soap
```

## Service Endpoints

Once running, the service provides:

- **WSDL**: http://localhost:8080/wsdl
- **SOAP Endpoint**: http://localhost:8080/soap
- **Health Check**: http://localhost:8080/health

## SOAP Operations

The service provides the following SOAP operations that mirror the original REST API:

### User Operations
- `GetAllUsers` - Get list of all users
- `CreateUser` - Create a new user account
- `GetUserById` - Get user details by ID
- `UpdateUser` - Update user information (requires authentication)
- `DeleteUser` - Delete user account (requires authentication)

### Session Operations
- `Login` - Authenticate user and receive token
- `Logout` - Invalidate authentication token

### Product Operations
- `GetAllProducts` - Get list of all products
- `CreateProduct` - Create a new product (requires authentication)
- `GetProductById` - Get product details by ID
- `UpdateProduct` - Update product information (requires authentication)
- `DeleteProduct` - Delete product (requires authentication)

### Order Operations
- `GetAllOrders` - Get user's orders (requires authentication)
- `CreateOrder` - Create a new order (requires authentication)
- `GetOrderById` - Get order details by ID (requires authentication)
- `UpdateOrder` - Update order information (requires authentication)
- `DeleteOrder` - Delete order (requires authentication)

## Authentication

The service uses JWT (JSON Web Tokens) for authentication. To authenticate:

1. Call the `Login` operation with valid credentials
2. Use the returned token in subsequent operations that require authentication
3. Include the token in the SOAP request as specified in the WSDL

## Client Examples

### Python Client

Run the included Python client example:

```bash
# Install client dependencies
pip install -r client/requirements.txt

# Run the example
python client/example.py
```

### Manual SOAP Request

Example SOAP request to create a user:

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:tns="http://cumroad.api.soap/service" 
               xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateUserRequest>
            <types:user>
                <types:email>user@example.com</types:email>
                <types:password>password123</types:password>
                <types:name>John Doe</types:name>
            </types:user>
        </types:CreateUserRequest>
    </soap:Body>
</soap:Envelope>
```

## Testing

### Automated Tests

Run the comprehensive test suite:

#### Windows (PowerShell):
```powershell
# Basic SOAP service tests
.\scripts\test.ps1

# REST vs SOAP response comparison (SOAP validation)
.\tests\compare-rest-soap.ps1
```

#### Linux/Mac:
```bash
# Basic tests (if available)
chmod +x tests/test.sh
./tests/test.sh

# REST vs SOAP comparison
chmod +x tests/compare-rest-soap.sh
./tests/compare-rest-soap.sh
```

### Test Types

1. **Basic Service Tests** (`scripts/test.ps1`):
   - Health check validation
   - WSDL availability
   - SOAP operations functionality
   - Python client integration

2. **Response Comparison Tests** (`tests/compare-rest-soap.ps1`):
   - Validates SOAP responses against expected formats
   - Compares with REST API responses (if available)
   - Shows equivalent data structures in different formats
   - **Note**: This test validates SOAP functionality even without REST API running

### Manual Testing

1. **Check service health:**
```bash
curl http://localhost:8080/health
```

2. **View WSDL:**
```bash
curl http://localhost:8080/wsdl
```

3. **Test SOAP endpoint with client:**
```bash
python client/example.py
```

## Error Handling

The service implements comprehensive error handling with SOAP faults that correspond to the original REST API error responses:

- **400 Bad Request** → Validation errors
- **401 Unauthorized** → Authentication required
- **403 Forbidden** → Insufficient permissions
- **404 Not Found** → Resource not found
- **409 Conflict** → Resource conflicts (e.g., duplicate email)
- **422 Unprocessable Entity** → Invalid input data
- **500 Internal Server Error** → Server errors

## Configuration

### Environment Variables

- `JWT_SECRET`: Secret key for JWT token signing (default: development key)
- `FLASK_ENV`: Flask environment (development/production)

### Database

The service uses SQLite for data persistence. The database file (`cumroad.db`) is created automatically in the working directory.

## API Comparison

| REST Endpoint | HTTP Method | SOAP Operation |
|---------------|-------------|----------------|
| `/users` | GET | GetAllUsers |
| `/users` | POST | CreateUser |
| `/users/{id}` | GET | GetUserById |
| `/users/{id}` | PATCH | UpdateUser |
| `/users/{id}` | DELETE | DeleteUser |
| `/sessions` | POST | Login |
| `/sessions` | DELETE | Logout |
| `/products` | GET | GetAllProducts |
| `/products` | POST | CreateProduct |
| `/products/{id}` | GET | GetProductById |
| `/products/{id}` | PATCH | UpdateProduct |
| `/products/{id}` | DELETE | DeleteProduct |
| `/orders` | GET | GetAllOrders |
| `/orders` | POST | CreateOrder |
| `/orders/{id}` | GET | GetOrderById |
| `/orders/{id}` | PATCH | UpdateOrder |
| `/orders/{id}` | DELETE | DeleteOrder |

## Troubleshooting

### Common Issues

1. **Port 8080 already in use:**
   - Stop any other services using port 8080
   - Or modify the port in `src/soap_service.py`

2. **Module not found errors:**
   - Ensure virtual environment is activated
   - Install dependencies: `pip install -r requirements.txt`

3. **Permission denied (Linux/Mac):**
   - Make scripts executable: `chmod +x scripts/run.sh tests/test.sh`

4. **WSDL validation errors:**
   - Check that the service is running
   - Verify network connectivity to localhost:8080

### Logs

- Service logs are output to console when running manually
- Docker logs: `docker-compose logs`
- Test logs are saved to `service.log` during automated testing

## Development

### Adding New Operations

1. Define the operation in the WSDL file (`wsdl/cumroad-api.wsdl`)
2. Implement the operation in the service class (`src/soap_service.py`)
3. Add tests for the new operation
4. Update this README

### Code Style

The project follows Python PEP 8 guidelines. Key points:
- Use descriptive variable names
- Include docstrings for all functions
- Handle errors gracefully with appropriate SOAP faults
- Log important operations and errors

## License

This project is created for educational purposes as part of a web services course assignment.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test output for specific error messages
3. Ensure all requirements are met and properly installed
