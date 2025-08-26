#!/usr/bin/env python3
"""
CumRoad SOAP Service Implementation
A SOAP service that replicates the functionality of the REST API
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
import hashlib
import jwt
import json
from dataclasses import dataclass, asdict
from flask import Flask, request
from flask_basicauth import BasicAuth
from spyne import Application, rpc, ServiceBase, Integer, Unicode, ComplexModel, Iterable, Fault, Boolean, Double, DateTime
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from werkzeug.serving import run_simple

# JWT Secret key (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')

# Database setup
DB_FILE = 'cumroad.db'

# Data Models
class User(ComplexModel):
    id = Integer
    email = Unicode
    name = Unicode
    role = Unicode  # 'user' or 'admin'
    created_at = DateTime
    updated_at = DateTime

class UserWithToken(ComplexModel):
    id = Integer
    email = Unicode
    name = Unicode
    role = Unicode
    created_at = DateTime
    updated_at = DateTime
    token = Unicode

class UserInput(ComplexModel):
    email = Unicode
    password = Unicode
    name = Unicode

class UserUpdateInput(ComplexModel):
    name = Unicode
    password = Unicode

class LoginInput(ComplexModel):
    email = Unicode
    password = Unicode

class Product(ComplexModel):
    id = Integer
    name = Unicode
    description = Unicode
    price = Double
    image_url = Unicode
    user_id = Integer
    created_at = DateTime
    updated_at = DateTime

class ProductInput(ComplexModel):
    name = Unicode
    description = Unicode
    price = Double
    image_url = Unicode

class ProductUpdateInput(ComplexModel):
    name = Unicode
    description = Unicode
    price = Double
    image_url = Unicode

class Order(ComplexModel):
    id = Integer
    user_id = Integer
    product_id = Integer
    quantity = Integer
    total_price = Double
    status = Unicode  # 'pending', 'completed', 'cancelled'
    created_at = DateTime
    updated_at = DateTime
    product = Product

class OrderInput(ComplexModel):
    product_id = Integer
    quantity = Integer

class OrderUpdateInput(ComplexModel):
    quantity = Integer
    status = Unicode

class ServiceFault(ComplexModel):
    type = Unicode
    title = Unicode
    status = Integer
    detail = Unicode
    instance = Unicode
    code = Integer
    field = Unicode

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

# SOAP Service Implementation
class CumRoadService(ServiceBase):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager(DB_FILE)
        self.auth = AuthManager()
    
    def _raise_soap_fault(self, status: int, title: str, detail: str, code: int = None, field: str = None):
        """Raise a SOAP fault with error details"""
        fault = ServiceFault()
        fault.type = f"https://docs.digikaup.online/errors/{title.lower().replace(' ', '-')}"
        fault.title = title
        fault.status = status
        fault.detail = detail
        fault.instance = "/soap"
        fault.code = code
        fault.field = field
        raise Fault('Client', detail)
    
    def _authenticate_user(self, token: str) -> Dict:
        """Authenticate user by token"""
        if not token:
            self._raise_soap_fault(401, "Authentication Required", "Authentication token is required", 2001)
        
        payload = self.auth.verify_token(token)
        if not payload:
            self._raise_soap_fault(401, "Invalid Token", "Authentication token is invalid or expired", 2002)
        
        return payload
    
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
    
    def _datetime_from_string(self, dt_str: str) -> datetime:
        """Convert string to datetime"""
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.utcnow()
    
    # User Operations
    @rpc(_returns=Iterable(User))
    def GetAllUsers(ctx):
        """Get all users"""
        self = ctx.service_class
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name, role, created_at, updated_at FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            user = User()
            user.id = row[0]
            user.email = row[1]
            user.name = row[2]
            user.role = row[3]
            user.created_at = self._datetime_from_string(row[4])
            user.updated_at = self._datetime_from_string(row[5])
            users.append(user)
        
        return users
    
    @rpc(UserInput, _returns=User)
    def CreateUser(ctx, user_input):
        """Create a new user"""
        self = ctx.service_class
        
        if not user_input.email or not user_input.password:
            self._raise_soap_fault(400, "Validation Error", "Email and password are required", 1001)
        
        if len(user_input.password) < 8:
            self._raise_soap_fault(422, "Invalid Password", "Password must be at least 8 characters long", 1002, "password")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_input.email,))
        if cursor.fetchone():
            conn.close()
            self._raise_soap_fault(409, "Email Already Registered", "The email address is already registered", 1003, "email")
        
        # Insert new user
        password_hash = self.auth.hash_password(user_input.password)
        name = user_input.name or user_input.email.split('@')[0]
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, role) 
            VALUES (?, ?, ?, 'user')
        """, (user_input.email, password_hash, name))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return created user
        user_data = self._get_user_by_id(user_id)
        user = User()
        user.id = user_data['id']
        user.email = user_data['email']
        user.name = user_data['name']
        user.role = user_data['role']
        user.created_at = self._datetime_from_string(user_data['created_at'])
        user.updated_at = self._datetime_from_string(user_data['updated_at'])
        
        return user
    
    @rpc(Integer, _returns=User)
    def GetUserById(ctx, user_id):
        """Get user by ID"""
        self = ctx.service_class
        user_data = self._get_user_by_id(user_id)
        
        if not user_data:
            self._raise_soap_fault(404, "Resource Not Found", "The requested user was not found", 3001)
        
        user = User()
        user.id = user_data['id']
        user.email = user_data['email']
        user.name = user_data['name']
        user.role = user_data['role']
        user.created_at = self._datetime_from_string(user_data['created_at'])
        user.updated_at = self._datetime_from_string(user_data['updated_at'])
        
        return user
    
    @rpc(Integer, UserUpdateInput, Unicode, _returns=User)
    def UpdateUser(ctx, user_id, user_update, token):
        """Update user"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        # Check if user exists
        user_data = self._get_user_by_id(user_id)
        if not user_data:
            self._raise_soap_fault(404, "Resource Not Found", "The requested user was not found", 3001)
        
        # Check authorization
        if payload['user_id'] != user_id and user_data['role'] != 'admin':
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Update user
        updates = []
        params = []
        
        if user_update.name:
            updates.append("name = ?")
            params.append(user_update.name)
        
        if user_update.password:
            if len(user_update.password) < 8:
                conn.close()
                self._raise_soap_fault(422, "Invalid Password", "Password must be at least 8 characters long", 1002, "password")
            updates.append("password_hash = ?")
            params.append(self.auth.hash_password(user_update.password))
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        
        # Return updated user
        user_data = self._get_user_by_id(user_id)
        user = User()
        user.id = user_data['id']
        user.email = user_data['email']
        user.name = user_data['name']
        user.role = user_data['role']
        user.created_at = self._datetime_from_string(user_data['created_at'])
        user.updated_at = self._datetime_from_string(user_data['updated_at'])
        
        return user
    
    @rpc(Integer, Unicode)
    def DeleteUser(ctx, user_id, token):
        """Delete user"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        # Check if user exists
        user_data = self._get_user_by_id(user_id)
        if not user_data:
            self._raise_soap_fault(404, "Resource Not Found", "The requested user was not found", 3001)
        
        # Check authorization
        if payload['user_id'] != user_id and user_data['role'] != 'admin':
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    # Session Operations
    @rpc(LoginInput, _returns=UserWithToken)
    def Login(ctx, credentials):
        """User login"""
        self = ctx.service_class
        
        if not credentials.email or not credentials.password:
            self._raise_soap_fault(400, "Validation Error", "Email and password are required", 1001)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, name, role, created_at, updated_at FROM users WHERE email = ?", 
                      (credentials.email,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not self.auth.verify_password(credentials.password, row[2]):
            self._raise_soap_fault(401, "Invalid Credentials", "Invalid email or password", 2001)
        
        # Generate token
        token = self.auth.generate_token(row[0], row[1])
        
        # Return user with token
        user = UserWithToken()
        user.id = row[0]
        user.email = row[1]
        user.name = row[3]
        user.role = row[4]
        user.created_at = self._datetime_from_string(row[5])
        user.updated_at = self._datetime_from_string(row[6])
        user.token = token
        
        return user
    
    @rpc(Unicode)
    def Logout(ctx, token):
        """User logout"""
        self = ctx.service_class
        # In a real implementation, you might want to blacklist the token
        # For now, we just validate it
        self._authenticate_user(token)
    
    # Product Operations
    @rpc(_returns=Iterable(Product))
    def GetAllProducts(ctx):
        """Get all products"""
        self = ctx.service_class
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products")
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            product = Product()
            product.id = row[0]
            product.name = row[1]
            product.description = row[2]
            product.price = row[3]
            product.image_url = row[4]
            product.user_id = row[5]
            product.created_at = self._datetime_from_string(row[6])
            product.updated_at = self._datetime_from_string(row[7])
            products.append(product)
        
        return products
    
    @rpc(ProductInput, Unicode, _returns=Product)
    def CreateProduct(ctx, product_input, token):
        """Create a new product"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        if not product_input.name or not product_input.price:
            self._raise_soap_fault(400, "Validation Error", "Name and price are required", 1001)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (name, description, price, image_url, user_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (product_input.name, product_input.description or '', 
              product_input.price, product_input.image_url or '', payload['user_id']))
        
        product_id = cursor.lastrowid
        conn.commit()
        
        # Get created product
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products WHERE id = ?", 
                      (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        product = Product()
        product.id = row[0]
        product.name = row[1]
        product.description = row[2]
        product.price = row[3]
        product.image_url = row[4]
        product.user_id = row[5]
        product.created_at = self._datetime_from_string(row[6])
        product.updated_at = self._datetime_from_string(row[7])
        
        return product
    
    @rpc(Integer, _returns=Product)
    def GetProductById(ctx, product_id):
        """Get product by ID"""
        self = ctx.service_class
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products WHERE id = ?", 
                      (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            self._raise_soap_fault(404, "Resource Not Found", "The requested product was not found", 3001)
        
        product = Product()
        product.id = row[0]
        product.name = row[1]
        product.description = row[2]
        product.price = row[3]
        product.image_url = row[4]
        product.user_id = row[5]
        product.created_at = self._datetime_from_string(row[6])
        product.updated_at = self._datetime_from_string(row[7])
        
        return product
    
    @rpc(Integer, ProductUpdateInput, Unicode, _returns=Product)
    def UpdateProduct(ctx, product_id, product_update, token):
        """Update product"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if product exists and user owns it
        cursor.execute("SELECT user_id FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            self._raise_soap_fault(404, "Resource Not Found", "The requested product was not found", 3001)
        
        if row[0] != payload['user_id']:
            conn.close()
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        # Update product
        updates = []
        params = []
        
        if product_update.name:
            updates.append("name = ?")
            params.append(product_update.name)
        
        if product_update.description is not None:
            updates.append("description = ?")
            params.append(product_update.description)
        
        if product_update.price:
            updates.append("price = ?")
            params.append(product_update.price)
        
        if product_update.image_url is not None:
            updates.append("image_url = ?")
            params.append(product_update.image_url)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(product_id)
            
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated product
        cursor.execute("SELECT id, name, description, price, image_url, user_id, created_at, updated_at FROM products WHERE id = ?", 
                      (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        product = Product()
        product.id = row[0]
        product.name = row[1]
        product.description = row[2]
        product.price = row[3]
        product.image_url = row[4]
        product.user_id = row[5]
        product.created_at = self._datetime_from_string(row[6])
        product.updated_at = self._datetime_from_string(row[7])
        
        return product
    
    @rpc(Integer, Unicode)
    def DeleteProduct(ctx, product_id, token):
        """Delete product"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if product exists and user owns it
        cursor.execute("SELECT user_id FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            self._raise_soap_fault(404, "Resource Not Found", "The requested product was not found", 3001)
        
        if row[0] != payload['user_id']:
            conn.close()
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()
    
    # Order Operations  
    @rpc(Unicode, _returns=Iterable(Order))
    def GetAllOrders(ctx, token):
        """Get all orders for authenticated user"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id, o.user_id, o.product_id, o.quantity, o.total_price, o.status, 
                   o.created_at, o.updated_at,
                   p.id, p.name, p.description, p.price, p.image_url, p.user_id, 
                   p.created_at, p.updated_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
        """, (payload['user_id'],))
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            order = Order()
            order.id = row[0]
            order.user_id = row[1]
            order.product_id = row[2]
            order.quantity = row[3]
            order.total_price = row[4]
            order.status = row[5]
            order.created_at = self._datetime_from_string(row[6])
            order.updated_at = self._datetime_from_string(row[7])
            
            # Product details
            product = Product()
            product.id = row[8]
            product.name = row[9]
            product.description = row[10]
            product.price = row[11]
            product.image_url = row[12]
            product.user_id = row[13]
            product.created_at = self._datetime_from_string(row[14])
            product.updated_at = self._datetime_from_string(row[15])
            order.product = product
            
            orders.append(order)
        
        return orders
    
    @rpc(OrderInput, Unicode, _returns=Order)
    def CreateOrder(ctx, order_input, token):
        """Create a new order"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        if not order_input.product_id or not order_input.quantity or order_input.quantity < 1:
            self._raise_soap_fault(400, "Validation Error", "Product ID and quantity (>= 1) are required", 1001)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id, price FROM products WHERE id = ?", (order_input.product_id,))
        product_row = cursor.fetchone()
        
        if not product_row:
            conn.close()
            self._raise_soap_fault(404, "Resource Not Found", "The requested product was not found", 3001)
        
        total_price = product_row[1] * order_input.quantity
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, quantity, total_price, status) 
            VALUES (?, ?, ?, ?, 'pending')
        """, (payload['user_id'], order_input.product_id, order_input.quantity, total_price))
        
        order_id = cursor.lastrowid
        conn.commit()
        
        # Get created order with product details
        cursor.execute("""
            SELECT o.id, o.user_id, o.product_id, o.quantity, o.total_price, o.status, 
                   o.created_at, o.updated_at,
                   p.id, p.name, p.description, p.price, p.image_url, p.user_id, 
                   p.created_at, p.updated_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        """, (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        order = Order()
        order.id = row[0]
        order.user_id = row[1]
        order.product_id = row[2]
        order.quantity = row[3]
        order.total_price = row[4]
        order.status = row[5]
        order.created_at = self._datetime_from_string(row[6])
        order.updated_at = self._datetime_from_string(row[7])
        
        # Product details
        product = Product()
        product.id = row[8]
        product.name = row[9]
        product.description = row[10]
        product.price = row[11]
        product.image_url = row[12]
        product.user_id = row[13]
        product.created_at = self._datetime_from_string(row[14])
        product.updated_at = self._datetime_from_string(row[15])
        order.product = product
        
        return order
    
    @rpc(Integer, Unicode, _returns=Order)
    def GetOrderById(ctx, order_id, token):
        """Get order by ID"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id, o.user_id, o.product_id, o.quantity, o.total_price, o.status, 
                   o.created_at, o.updated_at,
                   p.id, p.name, p.description, p.price, p.image_url, p.user_id, 
                   p.created_at, p.updated_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.id = ? AND o.user_id = ?
        """, (order_id, payload['user_id']))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            self._raise_soap_fault(404, "Resource Not Found", "The requested order was not found", 3001)
        
        order = Order()
        order.id = row[0]
        order.user_id = row[1]
        order.product_id = row[2]
        order.quantity = row[3]
        order.total_price = row[4]
        order.status = row[5]
        order.created_at = self._datetime_from_string(row[6])
        order.updated_at = self._datetime_from_string(row[7])
        
        # Product details
        product = Product()
        product.id = row[8]
        product.name = row[9]
        product.description = row[10]
        product.price = row[11]
        product.image_url = row[12]
        product.user_id = row[13]
        product.created_at = self._datetime_from_string(row[14])
        product.updated_at = self._datetime_from_string(row[15])
        order.product = product
        
        return order
    
    @rpc(Integer, OrderUpdateInput, Unicode, _returns=Order)
    def UpdateOrder(ctx, order_id, order_update, token):
        """Update order"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if order exists and user owns it
        cursor.execute("SELECT user_id, product_id, quantity FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            self._raise_soap_fault(404, "Resource Not Found", "The requested order was not found", 3001)
        
        if row[0] != payload['user_id']:
            conn.close()
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        # Update order
        updates = []
        params = []
        current_quantity = row[2]
        current_product_id = row[1]
        
        if order_update.quantity and order_update.quantity >= 1:
            updates.append("quantity = ?")
            params.append(order_update.quantity)
            current_quantity = order_update.quantity
            
            # Recalculate total price
            cursor.execute("SELECT price FROM products WHERE id = ?", (current_product_id,))
            price_row = cursor.fetchone()
            if price_row:
                new_total = price_row[0] * current_quantity
                updates.append("total_price = ?")
                params.append(new_total)
        
        if order_update.status and order_update.status in ['pending', 'completed', 'cancelled']:
            updates.append("status = ?")
            params.append(order_update.status)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(order_id)
            
            query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated order with product details
        cursor.execute("""
            SELECT o.id, o.user_id, o.product_id, o.quantity, o.total_price, o.status, 
                   o.created_at, o.updated_at,
                   p.id, p.name, p.description, p.price, p.image_url, p.user_id, 
                   p.created_at, p.updated_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        """, (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        order = Order()
        order.id = row[0]
        order.user_id = row[1]
        order.product_id = row[2]
        order.quantity = row[3]
        order.total_price = row[4]
        order.status = row[5]
        order.created_at = self._datetime_from_string(row[6])
        order.updated_at = self._datetime_from_string(row[7])
        
        # Product details
        product = Product()
        product.id = row[8]
        product.name = row[9]
        product.description = row[10]
        product.price = row[11]
        product.image_url = row[12]
        product.user_id = row[13]
        product.created_at = self._datetime_from_string(row[14])
        product.updated_at = self._datetime_from_string(row[15])
        order.product = product
        
        return order
    
    @rpc(Integer, Unicode)
    def DeleteOrder(ctx, order_id, token):
        """Delete order"""
        self = ctx.service_class
        payload = self._authenticate_user(token)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if order exists and user owns it
        cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            self._raise_soap_fault(404, "Resource Not Found", "The requested order was not found", 3001)
        
        if row[0] != payload['user_id']:
            conn.close()
            self._raise_soap_fault(403, "Unauthorized", "Not authorized to perform this action", 2003)
        
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()


def create_app():
    """Create Flask application with SOAP service"""
    app = Flask(__name__)
    
    # Create SOAP application
    soap_app = Application(
        [CumRoadService],
        tns='http://cumroad.api.soap/service',
        in_protocol=Soap11(validator='lxml'),
        out_protocol=Soap11()
    )
    
    # Create WSGI wrapper
    wsgi_app = WsgiApplication(soap_app)
    
    @app.route('/soap', methods=['POST', 'GET'])
    def soap_service():
        """Handle SOAP requests"""
        if request.method == 'GET':
            # Return WSDL
            response = wsgi_app._wsdl(request.environ, lambda status, headers: None)
            response_text = ''.join([chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk for chunk in response])
            return response_text, 200, {'Content-Type': 'text/xml; charset=utf-8'}
        else:
            # Handle SOAP request
            def start_response(status, headers):
                pass
            
            response = wsgi_app(request.environ, start_response)
            response_text = ''.join([chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk for chunk in response])
            return response_text, 200, {'Content-Type': 'text/xml; charset=utf-8'}
    
    @app.route('/wsdl')
    def get_wsdl():
        """Return WSDL file"""
        wsdl_path = os.path.join(os.path.dirname(__file__), '..', 'wsdl', 'cumroad-api.wsdl')
        try:
            with open(wsdl_path, 'r', encoding='utf-8') as f:
                wsdl_content = f.read()
            return wsdl_content, 200, {'Content-Type': 'text/xml; charset=utf-8'}
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
    run_simple('0.0.0.0', 8080, app, use_reloader=True, use_debugger=True)
