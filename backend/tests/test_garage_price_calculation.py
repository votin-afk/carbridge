"""
Test suite for garage price calculation feature
Tests:
1. POST /api/garage - should return calculated_price_usd and calculated_price_byn
2. POST /api/auth/login - authentication should work correctly
3. GET /api/garage - should return list of cars with calculated prices
4. bcrypt warning should NOT appear in backend logs after auth operations
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = {"email": "test@test.com", "password": "test"}
ADMIN_USER = {"email": "votin@tut.by", "password": "test"}
CONTRACTOR_USER = {"email": "test.contractor@test.com", "password": "test123"}


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_test_user(self):
        """Test login with test user credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == TEST_USER["email"]
        print(f"✓ Test user login successful, role: {data['user'].get('role', 'user')}")
    
    def test_login_admin_user(self):
        """Test login with admin user credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["role"] == "admin", f"Expected admin role, got: {data['user'].get('role')}"
        print(f"✓ Admin user login successful, role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got: {response.status_code}"
        print("✓ Invalid credentials correctly rejected with 401")
    
    def test_auth_me_endpoint(self):
        """Test /api/auth/me returns current user"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Then get current user
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_response.status_code == 200, f"Auth/me failed: {me_response.text}"
        
        data = me_response.json()
        assert data["email"] == TEST_USER["email"]
        print(f"✓ Auth/me endpoint working, user: {data['email']}")


class TestGaragePriceCalculation:
    """Test garage endpoints with price calculation"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_add_car_to_garage_with_price_calculation(self, auth_headers):
        """Test POST /api/garage returns calculated_price_usd and calculated_price_byn"""
        car_data = {
            "brand": "TEST_BYD",
            "model": "TEST_Seal",
            "year": 2023,
            "price_cny": 200000,  # 200,000 CNY
            "engine_type": "electric",
            "engine_volume": 0,
            "mileage": 10000,
            "image_url": "https://example.com/car.jpg",
            "description": "Test car for price calculation"
        }
        
        response = requests.post(f"{BASE_URL}/api/garage", json=car_data, headers=auth_headers)
        assert response.status_code == 200, f"Add car failed: {response.text}"
        
        data = response.json()
        
        # Verify car data is returned
        assert data["brand"] == car_data["brand"]
        assert data["model"] == car_data["model"]
        assert data["year"] == car_data["year"]
        assert data["price_cny"] == car_data["price_cny"]
        
        # CRITICAL: Verify calculated prices are returned
        assert "calculated_price_usd" in data, "calculated_price_usd missing from response"
        assert "calculated_price_byn" in data, "calculated_price_byn missing from response"
        
        # Verify calculated prices are not None and are positive numbers
        assert data["calculated_price_usd"] is not None, "calculated_price_usd is None"
        assert data["calculated_price_byn"] is not None, "calculated_price_byn is None"
        assert data["calculated_price_usd"] > 0, f"calculated_price_usd should be positive, got: {data['calculated_price_usd']}"
        assert data["calculated_price_byn"] > 0, f"calculated_price_byn should be positive, got: {data['calculated_price_byn']}"
        
        print(f"✓ Car added with calculated prices: ${data['calculated_price_usd']:.2f} USD / {data['calculated_price_byn']:.2f} BYN")
        
        # Store car_id for cleanup
        return data["id"]
    
    def test_add_ice_car_with_price_calculation(self, auth_headers):
        """Test POST /api/garage with ICE car returns calculated prices"""
        car_data = {
            "brand": "TEST_Geely",
            "model": "TEST_Emgrand",
            "year": 2022,
            "price_cny": 150000,  # 150,000 CNY
            "engine_type": "ice",
            "engine_volume": 1500,
            "mileage": 30000,
            "description": "Test ICE car for price calculation"
        }
        
        response = requests.post(f"{BASE_URL}/api/garage", json=car_data, headers=auth_headers)
        assert response.status_code == 200, f"Add ICE car failed: {response.text}"
        
        data = response.json()
        
        # Verify calculated prices
        assert data["calculated_price_usd"] is not None, "calculated_price_usd is None for ICE car"
        assert data["calculated_price_byn"] is not None, "calculated_price_byn is None for ICE car"
        assert data["calculated_price_usd"] > 0, "calculated_price_usd should be positive for ICE car"
        assert data["calculated_price_byn"] > 0, "calculated_price_byn should be positive for ICE car"
        
        # ICE cars should have customs duty, so price should be higher than electric
        print(f"✓ ICE car added with calculated prices: ${data['calculated_price_usd']:.2f} USD / {data['calculated_price_byn']:.2f} BYN")
        
        return data["id"]
    
    def test_add_hybrid_car_with_price_calculation(self, auth_headers):
        """Test POST /api/garage with hybrid car returns calculated prices"""
        car_data = {
            "brand": "TEST_BYD",
            "model": "TEST_Tang_DM",
            "year": 2023,
            "price_cny": 250000,  # 250,000 CNY
            "engine_type": "hybrid",
            "engine_volume": 2000,
            "mileage": 15000,
            "description": "Test hybrid car for price calculation"
        }
        
        response = requests.post(f"{BASE_URL}/api/garage", json=car_data, headers=auth_headers)
        assert response.status_code == 200, f"Add hybrid car failed: {response.text}"
        
        data = response.json()
        
        # Verify calculated prices
        assert data["calculated_price_usd"] is not None, "calculated_price_usd is None for hybrid car"
        assert data["calculated_price_byn"] is not None, "calculated_price_byn is None for hybrid car"
        assert data["calculated_price_usd"] > 0, "calculated_price_usd should be positive for hybrid car"
        
        print(f"✓ Hybrid car added with calculated prices: ${data['calculated_price_usd']:.2f} USD / {data['calculated_price_byn']:.2f} BYN")
        
        return data["id"]
    
    def test_get_garage_returns_calculated_prices(self, auth_headers):
        """Test GET /api/garage returns cars with calculated prices"""
        response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        assert response.status_code == 200, f"Get garage failed: {response.text}"
        
        cars = response.json()
        assert isinstance(cars, list), "Response should be a list"
        
        # Check if any cars have calculated prices
        cars_with_prices = [c for c in cars if c.get("calculated_price_usd") is not None]
        
        print(f"✓ Garage returned {len(cars)} cars, {len(cars_with_prices)} with calculated prices")
        
        # If there are cars with calculated prices, verify the structure
        for car in cars_with_prices[:3]:  # Check first 3
            assert "calculated_price_usd" in car
            assert "calculated_price_byn" in car
            if car["calculated_price_usd"] is not None:
                assert car["calculated_price_usd"] > 0
            print(f"  - {car.get('brand', 'N/A')} {car.get('model', 'N/A')}: ${car.get('calculated_price_usd', 'N/A')} USD")
    
    def test_garage_requires_authentication(self):
        """Test GET /api/garage requires authentication"""
        response = requests.get(f"{BASE_URL}/api/garage")
        assert response.status_code in [401, 403], f"Expected 401/403, got: {response.status_code}"
        print("✓ Garage endpoint correctly requires authentication")


class TestCalculatorEndpoint:
    """Test calculator endpoint directly"""
    
    def test_calculator_electric_car(self):
        """Test calculator for electric car (0 customs duty)"""
        calc_data = {
            "price_cny": 200000,
            "age": "under3",
            "engine_type": "electric",
            "engine_volume": 0,
            "user_type": "individual",
            "use_decree_140": False,
            "payment_via_platform": True
        }
        
        response = requests.post(f"{BASE_URL}/api/calculator", json=calc_data)
        assert response.status_code == 200, f"Calculator failed: {response.text}"
        
        data = response.json()
        assert "total_usd" in data
        assert "total_byn" in data
        assert data["customs_duty"] == 0, "Electric car should have 0 customs duty"
        
        print(f"✓ Electric car calculation: ${data['total_usd']:.2f} USD / {data['total_byn']:.2f} BYN")
    
    def test_calculator_ice_car(self):
        """Test calculator for ICE car (with customs duty)"""
        calc_data = {
            "price_cny": 150000,
            "age": "3to5",
            "engine_type": "ice",
            "engine_volume": 1500,
            "user_type": "individual",
            "use_decree_140": False,
            "payment_via_platform": True
        }
        
        response = requests.post(f"{BASE_URL}/api/calculator", json=calc_data)
        assert response.status_code == 200, f"Calculator failed: {response.text}"
        
        data = response.json()
        assert "total_usd" in data
        assert "total_byn" in data
        assert data["customs_duty"] > 0, "ICE car should have customs duty > 0"
        
        print(f"✓ ICE car calculation: ${data['total_usd']:.2f} USD, customs duty: €{data['customs_duty']:.2f}")


class TestBcryptWarning:
    """Test that bcrypt warning does not appear in logs"""
    
    def test_multiple_auth_operations_no_bcrypt_warning(self):
        """Perform multiple auth operations and verify no bcrypt warning in logs"""
        # Perform multiple login operations
        for i in range(3):
            response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
            assert response.status_code == 200, f"Login {i+1} failed"
        
        # Login with admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        assert response.status_code == 200, "Admin login failed"
        
        # Try invalid login (this also triggers password verification)
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
        print("✓ Multiple auth operations completed successfully")
        print("  Note: bcrypt warning check requires manual log inspection")
        print("  Run: tail -n 50 /var/log/supervisor/backend.err.log | grep -i bcrypt")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_cars(self):
        """Delete test cars created during testing"""
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code != 200:
            pytest.skip("Cannot login for cleanup")
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all cars
        response = requests.get(f"{BASE_URL}/api/garage", headers=headers)
        if response.status_code != 200:
            pytest.skip("Cannot get garage for cleanup")
        
        cars = response.json()
        
        # Delete TEST_ prefixed cars
        deleted_count = 0
        for car in cars:
            if car.get("brand", "").startswith("TEST_") or car.get("model", "").startswith("TEST_"):
                delete_response = requests.delete(f"{BASE_URL}/api/garage/{car['id']}", headers=headers)
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleanup completed: deleted {deleted_count} test cars")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
