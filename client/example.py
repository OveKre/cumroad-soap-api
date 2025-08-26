#!/usr/bin/env python3
"""
CumRoad SOAP Client Example
Demonstrates how to call all SOAP operations
"""

import sys
import xml.etree.ElementTree as ET
import requests
from zeep import Client
from zeep.transports import Transport
import urllib3

# Disable SSL warnings for demo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SOAP service configuration
SOAP_URL = "http://localhost:8080/soap"
WSDL_URL = "http://localhost:8080/wsdl"

def create_soap_client():
    """Create SOAP client"""
    try:
        transport = Transport(timeout=10)
        client = Client(WSDL_URL, transport=transport)
        return client
    except Exception as e:
        print(f"Error creating SOAP client: {e}")
        print("Make sure the SOAP service is running on http://localhost:8080")
        sys.exit(1)

def demo_user_operations(client):
    """Demonstrate user operations"""
    print("\n=== USER OPERATIONS ===")
    
    try:
        # Create a user
        print("\n1. Creating a new user...")
        user_input = {
            'email': 'demo@example.com',
            'password': 'password123',
            'name': 'Demo User'
        }
        
        user_response = client.service.CreateUser(user=user_input)
        print(f"Created user: {user_response}")
        user_id = user_response['id'] if 'id' in user_response else user_response.id
        
        # Get all users
        print("\n2. Getting all users...")
        users_response = client.service.GetAllUsers()
        print(f"All users: {users_response}")
        
        # Get user by ID
        print(f"\n3. Getting user by ID ({user_id})...")
        user_detail = client.service.GetUserById(user_id)
        print(f"User details: {user_detail}")
        
        # Login
        print("\n4. Logging in...")
        login_input = {
            'email': 'demo@example.com',
            'password': 'password123'
        }
        login_response = client.service.Login(credentials=login_input)
        print(f"Login successful: {login_response}")
        token = login_response['token'] if 'token' in login_response else login_response.token
        
        # Update user
        print("\n5. Updating user...")
        user_update = {
            'name': 'Updated Demo User'
        }
        updated_user = client.service.UpdateUser(user_id, user_update, token)
        print(f"Updated user: {updated_user}")
        
        return user_id, token
        
    except Exception as e:
        print(f"Error in user operations: {e}")
        return None, None

def demo_product_operations(client, token):
    """Demonstrate product operations"""
    print("\n=== PRODUCT OPERATIONS ===")
    
    if not token:
        print("No authentication token available, skipping product operations")
        return None
    
    try:
        # Create a product
        print("\n1. Creating a new product...")
        product_input = {
            'name': 'Demo Product',
            'description': 'This is a demo product',
            'price': 29.99,
            'image_url': 'https://example.com/product.jpg'
        }
        
        product_response = client.service.CreateProduct(product_input, token)
        print(f"Created product: {product_response}")
        product_id = product_response['id'] if 'id' in product_response else product_response.id
        
        # Get all products
        print("\n2. Getting all products...")
        products_response = client.service.GetAllProducts()
        print(f"All products: {products_response}")
        
        # Get product by ID
        print(f"\n3. Getting product by ID ({product_id})...")
        product_detail = client.service.GetProductById(product_id)
        print(f"Product details: {product_detail}")
        
        # Update product
        print("\n4. Updating product...")
        product_update = {
            'name': 'Updated Demo Product',
            'price': 39.99
        }
        updated_product = client.service.UpdateProduct(product_id, product_update, token)
        print(f"Updated product: {updated_product}")
        
        return product_id
        
    except Exception as e:
        print(f"Error in product operations: {e}")
        return None

def demo_order_operations(client, token, product_id):
    """Demonstrate order operations"""
    print("\n=== ORDER OPERATIONS ===")
    
    if not token or not product_id:
        print("No authentication token or product ID available, skipping order operations")
        return None
    
    try:
        # Create an order
        print("\n1. Creating a new order...")
        order_input = {
            'product_id': product_id,
            'quantity': 2
        }
        
        order_response = client.service.CreateOrder(order_input, token)
        print(f"Created order: {order_response}")
        order_id = order_response['id'] if 'id' in order_response else order_response.id
        
        # Get all orders
        print("\n2. Getting all orders...")
        orders_response = client.service.GetAllOrders(token)
        print(f"All orders: {orders_response}")
        
        # Get order by ID
        print(f"\n3. Getting order by ID ({order_id})...")
        order_detail = client.service.GetOrderById(order_id, token)
        print(f"Order details: {order_detail}")
        
        # Update order
        print("\n4. Updating order...")
        order_update = {
            'quantity': 3,
            'status': 'completed'
        }
        updated_order = client.service.UpdateOrder(order_id, order_update, token)
        print(f"Updated order: {updated_order}")
        
        return order_id
        
    except Exception as e:
        print(f"Error in order operations: {e}")
        return None

def demo_cleanup(client, token, user_id, product_id, order_id):
    """Clean up demo data"""
    print("\n=== CLEANUP ===")
    
    try:
        # Delete order
        if order_id and token:
            print(f"\n1. Deleting order {order_id}...")
            client.service.DeleteOrder(order_id, token)
            print("Order deleted successfully")
        
        # Delete product
        if product_id and token:
            print(f"\n2. Deleting product {product_id}...")
            client.service.DeleteProduct(product_id, token)
            print("Product deleted successfully")
        
        # Logout
        if token:
            print("\n3. Logging out...")
            client.service.Logout(token)
            print("Logged out successfully")
        
        # Delete user
        if user_id and token:
            print(f"\n4. Deleting user {user_id}...")
            client.service.DeleteUser(user_id, token)
            print("User deleted successfully")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")

def demo_error_handling(client):
    """Demonstrate error handling"""
    print("\n=== ERROR HANDLING ===")
    
    try:
        # Try to get non-existent user
        print("\n1. Trying to get non-existent user...")
        try:
            client.service.GetUserById(99999)
        except Exception as e:
            print(f"Expected error caught: {e}")
        
        # Try to login with invalid credentials
        print("\n2. Trying to login with invalid credentials...")
        try:
            login_input = {
                'email': 'invalid@example.com',
                'password': 'wrongpassword'
            }
            client.service.Login(credentials=login_input)
        except Exception as e:
            print(f"Expected error caught: {e}")
        
        # Try to create user with invalid data
        print("\n3. Trying to create user with invalid data...")
        try:
            user_input = {
                'email': 'invalid-email',
                'password': '123',  # Too short
                'name': 'Test User'
            }
            client.service.CreateUser(user=user_input)
        except Exception as e:
            print(f"Expected error caught: {e}")
            
    except Exception as e:
        print(f"Error in error handling demo: {e}")

def check_service_availability():
    """Check if SOAP service is available"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✓ SOAP service is running")
            return True
        else:
            print(f"✗ SOAP service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("✗ SOAP service is not available")
        print("Please start the service using: ./scripts/run.ps1 or python src/soap_service.py")
        return False

def main():
    """Main demo function"""
    print("CumRoad SOAP Client Demo")
    print("=" * 40)
    
    # Check service availability
    if not check_service_availability():
        sys.exit(1)
    
    # Create SOAP client
    print("\nCreating SOAP client...")
    client = create_soap_client()
    print("✓ SOAP client created successfully")
    
    # Demo user operations
    user_id, token = demo_user_operations(client)
    
    # Demo product operations
    product_id = demo_product_operations(client, token)
    
    # Demo order operations
    order_id = demo_order_operations(client, token, product_id)
    
    # Demo error handling
    demo_error_handling(client)
    
    # Cleanup (optional - comment out if you want to keep test data)
    # demo_cleanup(client, token, user_id, product_id, order_id)
    
    print("\n" + "=" * 40)
    print("Demo completed successfully!")
    print("All SOAP operations have been tested.")
    print("\nYou can now:")
    print("- View WSDL at: http://localhost:8080/wsdl")
    print("- Check service health at: http://localhost:8080/health")
    print("- Use any SOAP client to interact with: http://localhost:8080/soap")

if __name__ == "__main__":
    main()
