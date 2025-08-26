#!/usr/bin/env python3
"""
CumRoad SOAP Service Implementation (Simplified)
A simple Flask-based SOAP service that replicates the functionality of the REST API
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
import hashlib
import jwt
import json
from flask import Flask, request, Response
import xml.etree.ElementTree as ET

# JWT Secret key (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')

# Database setup
DB_FILE = 'cumroad.db'

# Database Helper Class
class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)

# Authentication Helper
class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password against hash"""
        return AuthManager.hash_password(password) == hash
    
    @staticmethod
    def generate_token(user_id: int, email: str) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# SOAP Service Helper
class SOAPHelper:
    @staticmethod
    def create_soap_fault(fault_code: str, fault_string: str, detail: str = None) -> str:
        """Create SOAP fault response"""
        fault_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>{fault_code}</faultcode>
            <faultstring>{fault_string}</faultstring>'''
        
        if detail:
            fault_xml += f'''
            <detail>
                <error>{detail}</error>
            </detail>'''
        
        fault_xml += '''
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
        
        return fault_xml
    
    @staticmethod
    def parse_soap_request(soap_body: str) -> Dict:
        """Parse SOAP request and extract operation and parameters"""
        try:
            root = ET.fromstring(soap_body)
            # Find the operation in SOAP body
            for child in root:
                if 'Body' in child.tag:
                    for operation in child:
                        operation_name = operation.tag.split('}')[-1] if '}' in operation.tag else operation.tag
                        params = {}
                        for param in operation:
                            param_name = param.tag.split('}')[-1] if '}' in param.tag else param.tag
                            if len(param) > 0:  # Complex parameter
                                param_value = {}
                                for sub_param in param:
                                    sub_name = sub_param.tag.split('}')[-1] if '}' in sub_param.tag else sub_param.tag
                                    param_value[sub_name] = sub_param.text
                                params[param_name] = param_value
                            else:  # Simple parameter
                                params[param_name] = param.text
                        return {'operation': operation_name, 'params': params}
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}")
        
        raise ValueError("No operation found in SOAP request")

# SOAP Service Implementation
class CumRoadSOAPService:
    def __init__(self):
        self.db = DatabaseManager(DB_FILE)
        self.auth = AuthManager()
        self.soap_helper = SOAPHelper()
    
    def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID from database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, role, created_at, updated_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'role': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }
        return None
    
    def create_user(self, params: Dict) -> str:
        """Create a new user"""
        user_data = params.get('user', {})
        email = user_data.get('email')
        password = user_data.get('password')
        name = user_data.get('name', email.split('@')[0] if email else 'User')
        
        if not email or not password:
            return self.soap_helper.create_soap_fault("Client", "Validation Error", "Email and password are required")
        
        if len(password) < 8:
            return self.soap_helper.create_soap_fault("Client", "Invalid Password", "Password must be at least 8 characters long")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return self.soap_helper.create_soap_fault("Client", "Email Already Registered", "The email address is already registered")
        
        # Insert new user
        password_hash = self.auth.hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, role) 
            VALUES (?, ?, ?, 'user')
        """, (email, password_hash, name))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return created user
        user = self._get_user_by_id(user_id)
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateUserResponse>
            <types:user>
                <types:id>{user['id']}</types:id>
                <types:email>{user['email']}</types:email>
                <types:name>{user['name']}</types:name>
                <types:role>{user['role']}</types:role>
                <types:created_at>{user['created_at']}</types:created_at>
                <types:updated_at>{user['updated_at']}</types:updated_at>
            </types:user>
        </types:CreateUserResponse>
    </soap:Body>
</soap:Envelope>'''
    
    def get_all_users(self, params: Dict) -> str:
        """Get all users"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, role, created_at, updated_at FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        users_xml = ""
        for row in rows:
            users_xml += f'''
                <types:user>
                    <types:id>{row[0]}</types:id>
                    <types:email>{row[1]}</types:email>
                    <types:name>{row[2]}</types:name>
                    <types:role>{row[3]}</types:role>
                    <types:created_at>{row[4]}</types:created_at>
                    <types:updated_at>{row[5]}</types:updated_at>
                </types:user>'''
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllUsersResponse>
            <types:users>{users_xml}
            </types:users>
        </types:GetAllUsersResponse>
    </soap:Body>
</soap:Envelope>'''
    
    def login(self, params: Dict) -> str:
        """User login"""
        credentials = params.get('credentials', {})
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            return self.soap_helper.create_soap_fault("Client", "Validation Error", "Email and password are required")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, name, role, created_at, updated_at FROM users WHERE email = ?", 
                      (email,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not self.auth.verify_password(password, row[2]):
            return self.soap_helper.create_soap_fault("Client", "Invalid Credentials", "Invalid email or password")
        
        # Generate token
        token = self.auth.generate_token(row[0], row[1])
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:LoginResponse>
            <types:user>
                <types:id>{row[0]}</types:id>
                <types:email>{row[1]}</types:email>
                <types:name>{row[3]}</types:name>
                <types:role>{row[4]}</types:role>
                <types:created_at>{row[5]}</types:created_at>
                <types:updated_at>{row[6]}</types:updated_at>
                <types:token>{token}</types:token>
            </types:user>
        </types:LoginResponse>
    </soap:Body>
</soap:Envelope>'''
    
    def get_all_products(self, params: Dict) -> str:
        """Get all products"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products")
        rows = cursor.fetchall()
        conn.close()
        
        products_xml = ""
        for row in rows:
            products_xml += f'''
                <types:product>
                    <types:id>{row[0]}</types:id>
                    <types:name>{row[1]}</types:name>
                    <types:description>{row[2] or ''}</types:description>
                    <types:price>{row[3]}</types:price>
                    <types:image_url>{row[4] or ''}</types:image_url>
                    <types:user_id>{row[5]}</types:user_id>
                    <types:created_at>{row[6]}</types:created_at>
                    <types:updated_at>{row[7]}</types:updated_at>
                </types:product>'''
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:GetAllProductsResponse>
            <types:products>{products_xml}
            </types:products>
        </types:GetAllProductsResponse>
    </soap:Body>
</soap:Envelope>'''
    
    def create_product(self, params: Dict) -> str:
        """Create a new product"""
        product_data = params.get('product', {})
        token = params.get('token')
        
        if not token:
            return self.soap_helper.create_soap_fault("Client", "Authentication Required", "Authentication token is required")
        
        payload = self.auth.verify_token(token)
        if not payload:
            return self.soap_helper.create_soap_fault("Client", "Invalid Token", "Authentication token is invalid or expired")
        
        name = product_data.get('name')
        description = product_data.get('description', '')
        price = product_data.get('price')
        image_url = product_data.get('image_url', '')
        
        if not name or not price:
            return self.soap_helper.create_soap_fault("Client", "Validation Error", "Name and price are required")
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            return self.soap_helper.create_soap_fault("Client", "Validation Error", "Invalid price format")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (name, description, price, image_url, user_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, price, image_url, payload['user_id']))
        
        product_id = cursor.lastrowid
        conn.commit()
        
        # Get created product
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products WHERE id = ?", 
                      (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:types="http://cumroad.api.soap/types">
    <soap:Body>
        <types:CreateProductResponse>
            <types:product>
                <types:id>{row[0]}</types:id>
                <types:name>{row[1]}</types:name>
                <types:description>{row[2] or ''}</types:description>
                <types:price>{row[3]}</types:price>
                <types:image_url>{row[4] or ''}</types:image_url>
                <types:user_id>{row[5]}</types:user_id>
                <types:created_at>{row[6]}</types:created_at>
                <types:updated_at>{row[7]}</types:updated_at>
            </types:product>
        </types:CreateProductResponse>
    </soap:Body>
</soap:Envelope>'''
    
    def process_request(self, soap_body: str) -> str:
        """Process SOAP request and return response"""
        try:
            parsed = self.soap_helper.parse_soap_request(soap_body)
            operation = parsed['operation']
            params = parsed['params']
            
            # Route to appropriate method
            if operation == 'CreateUserRequest':
                return self.create_user(params)
            elif operation == 'GetAllUsersRequest':
                return self.get_all_users(params)
            elif operation == 'LoginRequest':
                return self.login(params)
            elif operation == 'GetAllProductsRequest':
                return self.get_all_products(params)
            elif operation == 'CreateProductRequest':
                return self.create_product(params)
            else:
                return self.soap_helper.create_soap_fault("Client", "Unknown Operation", f"Operation {operation} is not supported")
                
        except Exception as e:
            return self.soap_helper.create_soap_fault("Server", "Internal Error", str(e))

def create_app():
    """Create Flask application with SOAP service"""
    app = Flask(__name__)
    soap_service = CumRoadSOAPService()
    
    @app.route('/soap', methods=['POST', 'GET'])
    def soap_endpoint():
        """Handle SOAP requests"""
        if request.method == 'GET':
            # Return simplified WSDL
            wsdl_path = os.path.join(os.path.dirname(__file__), '..', 'wsdl', 'cumroad-api.wsdl')
            try:
                with open(wsdl_path, 'r', encoding='utf-8') as f:
                    wsdl_content = f.read()
                return Response(wsdl_content, mimetype='text/xml')
            except FileNotFoundError:
                return "WSDL file not found", 404
        else:
            # Handle SOAP request
            soap_body = request.get_data(as_text=True)
            response_xml = soap_service.process_request(soap_body)
            return Response(response_xml, mimetype='text/xml; charset=utf-8')
    
    @app.route('/wsdl')
    def get_wsdl():
        """Return WSDL file"""
        wsdl_path = os.path.join(os.path.dirname(__file__), '..', 'wsdl', 'cumroad-api.wsdl')
        try:
            with open(wsdl_path, 'r', encoding='utf-8') as f:
                wsdl_content = f.read()
            return Response(wsdl_content, mimetype='text/xml')
        except FileNotFoundError:
            return "WSDL file not found", 404
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return {"status": "ok", "service": "CumRoad SOAP API"}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting CumRoad SOAP Service on http://0.0.0.0:8080")
    print("WSDL available at: http://localhost:8080/wsdl")
    print("SOAP endpoint: http://localhost:8080/soap")
    print("Health check: http://localhost:8080/health")
    print("Press Ctrl+C to stop the service")
    app.run(host='0.0.0.0', port=8080, debug=True)
