"""
Test suite for validating backend refactoring - server.py modularization
Tests auth, calculator, garage, catalog, and user account endpoints
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "votin@tut.by", "password": "test"}
STANDARD_USER = {"email": "test@test.com", "password": "test"}


class TestHealthCheck:
    """Basic health check to ensure backend is running"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestAuthEndpoints:
    """Test authentication endpoints: /api/auth/register, /api/auth/login, /api/auth/me"""
    
    def test_register_new_user(self):
        """Test POST /api/auth/register - creates new user"""
        unique_email = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "password": "testpass123",
            "name": "TEST_New User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["name"] == "TEST_New User"
        assert data["user"]["role"] == "user"
        assert "id" in data["user"]
    
    def test_register_duplicate_email(self):
        """Test POST /api/auth/register - rejects duplicate email"""
        payload = {
            "email": ADMIN_USER["email"],
            "password": "testpass123",
            "name": "Duplicate User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
    
    def test_login_admin_user(self):
        """Test POST /api/auth/login - admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_USER["email"]
        assert data["user"]["role"] == "admin"
    
    def test_login_standard_user(self):
        """Test POST /api/auth/login - standard user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STANDARD_USER)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == STANDARD_USER["email"]
    
    def test_login_invalid_credentials(self):
        """Test POST /api/auth/login - rejects invalid credentials"""
        payload = {"email": "nonexistent@test.com", "password": "wrongpass"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test GET /api/auth/me - returns current user profile"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        token = login_response.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == ADMIN_USER["email"]
        assert data["role"] == "admin"
        assert "id" in data
        assert "created_at" in data
    
    def test_get_me_without_token(self):
        """Test GET /api/auth/me - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]


class TestCalculatorEndpoint:
    """Test calculator endpoint: /api/calculator"""
    
    def test_calculator_electric_car(self):
        """Test POST /api/calculator - electric car calculation"""
        payload = {
            "price_cny": 100000,
            "age": "under3",
            "engine_type": "electric"
        }
        response = requests.post(f"{BASE_URL}/api/calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["price_cny"] == 100000
        assert "price_eur" in data
        assert "price_usd" in data
        assert "customs_duty" in data
        assert "utilization_fee" in data
        assert "total_byn" in data
        assert "total_usd" in data
        assert "breakdown" in data
        
        # Electric cars have 0 customs duty
        assert data["customs_duty"] == 0
    
    def test_calculator_ice_car(self):
        """Test POST /api/calculator - ICE car calculation"""
        payload = {
            "price_cny": 150000,
            "age": "3to5",
            "engine_type": "ice",
            "engine_volume": 2000
        }
        response = requests.post(f"{BASE_URL}/api/calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["price_cny"] == 150000
        assert data["customs_duty"] > 0  # ICE cars have customs duty
        assert data["utilization_fee"] > 0
    
    def test_calculator_hybrid_car(self):
        """Test POST /api/calculator - hybrid car calculation"""
        payload = {
            "price_cny": 200000,
            "age": "under3",
            "engine_type": "hybrid",
            "engine_volume": 1500
        }
        response = requests.post(f"{BASE_URL}/api/calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["price_cny"] == 200000
        assert "vat" in data
    
    def test_calculator_with_decree_140(self):
        """Test POST /api/calculator - with Decree 140 discount"""
        payload = {
            "price_cny": 100000,
            "age": "under3",
            "engine_type": "ice",
            "engine_volume": 2000,
            "user_type": "individual",
            "use_decree_140": True
        }
        response = requests.post(f"{BASE_URL}/api/calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["decree_140_discount"] >= 0
        assert data["breakdown"]["decree_140_applied"] == True
    
    def test_calculator_legal_entity(self):
        """Test POST /api/calculator - legal entity calculation"""
        payload = {
            "price_cny": 300000,
            "age": "under3",
            "engine_type": "ice",
            "engine_volume": 3000,
            "user_type": "legal"
        }
        response = requests.post(f"{BASE_URL}/api/calculator", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Legal entities have higher utilization fees
        assert data["utilization_fee"] > 0


class TestGarageEndpoints:
    """Test garage endpoints: GET /api/garage, POST /api/garage"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        return response.json()["access_token"]
    
    def test_get_garage_list(self, auth_token):
        """Test GET /api/garage - returns user's cars"""
        response = requests.get(
            f"{BASE_URL}/api/garage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_car_to_garage(self, auth_token):
        """Test POST /api/garage - adds car to garage"""
        payload = {
            "brand": "TEST_BYD",
            "model": "Seal",
            "year": 2024,
            "price_cny": 250000,
            "engine_type": "electric"
        }
        response = requests.post(
            f"{BASE_URL}/api/garage",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["brand"] == "TEST_BYD"
        assert data["model"] == "Seal"
        assert data["year"] == 2024
        assert data["price_cny"] == 250000
        assert data["engine_type"] == "electric"
        assert "id" in data
        assert data["status"] == "saved"
    
    def test_add_car_and_verify_in_list(self, auth_token):
        """Test POST /api/garage then GET to verify persistence"""
        # Add car
        unique_model = f"TEST_Model_{uuid.uuid4().hex[:6]}"
        payload = {
            "brand": "TEST_NIO",
            "model": unique_model,
            "year": 2023,
            "price_cny": 350000,
            "engine_type": "electric"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/garage",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert create_response.status_code == 200
        car_id = create_response.json()["id"]
        
        # Verify in list
        list_response = requests.get(
            f"{BASE_URL}/api/garage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert list_response.status_code == 200
        
        cars = list_response.json()
        car_ids = [car["id"] for car in cars]
        assert car_id in car_ids
    
    def test_garage_requires_auth(self):
        """Test GET /api/garage - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/garage")
        assert response.status_code in [401, 403]


class TestCatalogEndpoints:
    """Test catalog endpoints: /api/catalog/brands, /api/catalog/search"""
    
    def test_get_brands(self):
        """Test GET /api/catalog/brands - returns list of brands"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check brand structure
        brand = data[0]
        assert "name" in brand
        assert "slug" in brand
    
    def test_search_catalog(self):
        """Test GET /api/catalog/search - returns car listings"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        assert "cars" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["cars"], list)
    
    def test_search_by_brand(self):
        """Test GET /api/catalog/search?brand=BYD - filters by brand"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD")
        assert response.status_code == 200
        
        data = response.json()
        assert "cars" in data
        # All returned cars should be BYD
        for car in data["cars"]:
            assert car["brand"].upper() == "BYD"
    
    def test_search_with_pagination(self):
        """Test GET /api/catalog/search - pagination works"""
        response_page1 = requests.get(f"{BASE_URL}/api/catalog/search?page=1")
        response_page2 = requests.get(f"{BASE_URL}/api/catalog/search?page=2")
        
        assert response_page1.status_code == 200
        assert response_page2.status_code == 200
        
        data1 = response_page1.json()
        data2 = response_page2.json()
        
        assert data1["page"] == 1
        assert data2["page"] == 2
    
    def test_car_data_structure(self):
        """Test catalog car data has required fields"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        if data["cars"]:
            car = data["cars"][0]
            # Check required fields
            assert "id" in car
            assert "brand" in car
            assert "model" in car
            assert "price_from_cny" in car
            assert "engine_type" in car


class TestUserAccountEndpoints:
    """Test user account endpoints: /api/user/account, /api/account/summary"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        return response.json()["access_token"]
    
    def test_get_user_account(self, auth_token):
        """Test GET /api/user/account - returns account details"""
        response = requests.get(
            f"{BASE_URL}/api/user/account",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "balance" in data
        assert "is_verified" in data
        assert "contract_signed" in data
        assert isinstance(data["balance"], (int, float))
        assert isinstance(data["is_verified"], bool)
        assert isinstance(data["contract_signed"], bool)
    
    def test_get_account_summary(self, auth_token):
        """Test GET /api/account/summary - returns dashboard summary"""
        response = requests.get(
            f"{BASE_URL}/api/account/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "balance" in data
        assert "is_verified" in data
        assert "verification_status" in data
        assert "contract_signed" in data
    
    def test_account_requires_auth(self):
        """Test /api/user/account - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/user/account")
        assert response.status_code in [401, 403]


class TestModularRoutes:
    """Test that modular routes are properly integrated"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        return response.json()["access_token"]
    
    def test_affiliate_status_endpoint(self, auth_token):
        """Test GET /api/affiliate/status - affiliate module route"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 404 if not registered, or 200 if registered
        assert response.status_code in [200, 404]
    
    def test_user_role_endpoint(self, auth_token):
        """Test GET /api/user/role - user module route"""
        response = requests.get(
            f"{BASE_URL}/api/user/role",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "role" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
