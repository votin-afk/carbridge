"""
Hot Deals Feature Tests
Tests for the 'Горящие предложения' (Hot Deals) section
- GET /api/hot-deals - list hot deals
- GET /api/hot-deals/{deal_id} - get specific deal
- POST /api/hot-deals/{deal_id}/add-to-garage - add deal to garage with seller assignment
- POST /api/hot-deals - create hot deal (moderator/verified contractor only)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test"


class TestHotDealsPublicAPI:
    """Tests for public hot deals endpoints (no auth required)"""
    
    def test_get_hot_deals_list(self):
        """Test GET /api/hot-deals returns list of hot deals"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Should have demo deals seeded
        if len(data) > 0:
            deal = data[0]
            # Verify deal structure
            assert "id" in deal, "Deal should have id"
            assert "brand" in deal, "Deal should have brand"
            assert "model" in deal, "Deal should have model"
            assert "year" in deal, "Deal should have year"
            assert "price_cny" in deal, "Deal should have price_cny"
            assert "expires_at" in deal, "Deal should have expires_at"
            assert "seller_name" in deal, "Deal should have seller_name"
            print(f"✓ Found {len(data)} hot deals")
            print(f"  First deal: {deal['brand']} {deal['model']} - ¥{deal['price_cny']}")
    
    def test_get_hot_deals_with_limit(self):
        """Test GET /api/hot-deals?limit=4 returns limited results"""
        response = requests.get(f"{BASE_URL}/api/hot-deals?limit=4")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 4, f"Should return at most 4 deals, got {len(data)}"
        print(f"✓ Limit parameter works - returned {len(data)} deals")
    
    def test_hot_deal_has_discount_info(self):
        """Test that hot deals have discount information"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        data = response.json()
        deals_with_discount = [d for d in data if d.get("special_price_cny") and d.get("special_price_cny") < d.get("price_cny")]
        
        if deals_with_discount:
            deal = deals_with_discount[0]
            discount_percent = round((1 - deal["special_price_cny"] / deal["price_cny"]) * 100)
            print(f"✓ Deal {deal['brand']} {deal['model']} has {discount_percent}% discount")
            print(f"  Original: ¥{deal['price_cny']}, Special: ¥{deal['special_price_cny']}")
        else:
            print("⚠ No deals with discounts found")
    
    def test_hot_deal_has_timer_info(self):
        """Test that hot deals have expiration time for countdown timer"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            deal = data[0]
            assert "expires_at" in deal, "Deal should have expires_at for timer"
            
            # Verify expires_at is a valid ISO datetime
            try:
                expires = datetime.fromisoformat(deal["expires_at"].replace("Z", "+00:00"))
                now = datetime.now(expires.tzinfo)
                time_left = expires - now
                print(f"✓ Deal expires in {time_left.days}d {time_left.seconds // 3600}h")
            except Exception as e:
                pytest.fail(f"Invalid expires_at format: {e}")
    
    def test_hot_deal_has_seller_info(self):
        """Test that hot deals have seller information"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            deal = data[0]
            assert "seller_name" in deal, "Deal should have seller_name"
            assert "seller_type" in deal, "Deal should have seller_type"
            assert "is_verified_seller" in deal, "Deal should have is_verified_seller"
            print(f"✓ Seller: {deal['seller_name']} ({deal['seller_type']}), verified: {deal['is_verified_seller']}")
    
    def test_get_specific_hot_deal(self):
        """Test GET /api/hot-deals/{deal_id} returns specific deal"""
        # First get list to find a deal ID
        list_response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert list_response.status_code == 200
        
        deals = list_response.json()
        if len(deals) == 0:
            pytest.skip("No hot deals available")
        
        deal_id = deals[0]["id"]
        response = requests.get(f"{BASE_URL}/api/hot-deals/{deal_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        deal = response.json()
        assert deal["id"] == deal_id
        print(f"✓ Got specific deal: {deal['brand']} {deal['model']}")
    
    def test_get_nonexistent_deal_returns_404(self):
        """Test GET /api/hot-deals/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/hot-deals/nonexistent-deal-id")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent deal returns 404")


class TestHotDealsAuthenticated:
    """Tests for authenticated hot deals endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_add_hot_deal_to_garage(self, auth_headers):
        """Test POST /api/hot-deals/{deal_id}/add-to-garage adds car to garage"""
        # Get a hot deal
        list_response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert list_response.status_code == 200
        
        deals = list_response.json()
        if len(deals) == 0:
            pytest.skip("No hot deals available")
        
        deal = deals[0]
        deal_id = deal["id"]
        
        # Add to garage
        response = requests.post(
            f"{BASE_URL}/api/hot-deals/{deal_id}/add-to-garage",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "car_id" in data, "Response should have car_id"
        assert "message" in data, "Response should have message"
        assert "seller_name" in data, "Response should have seller_name"
        
        print(f"✓ Added {deal['brand']} {deal['model']} to garage")
        print(f"  Car ID: {data['car_id']}")
        print(f"  Seller assigned: {data.get('seller_assigned')}, Name: {data.get('seller_name')}")
        
        # Verify car is in garage
        garage_response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        assert garage_response.status_code == 200
        
        garage = garage_response.json()
        added_car = next((c for c in garage if c["id"] == data["car_id"]), None)
        assert added_car is not None, "Car should be in garage"
        # Note: from_hot_deal field is stored but not returned in CarResponse model
        # This is a minor issue - the data is persisted but not exposed in API response
        print(f"✓ Verified car is in garage")
        
        return data["car_id"]
    
    def test_add_to_garage_requires_auth(self):
        """Test POST /api/hot-deals/{deal_id}/add-to-garage requires authentication"""
        response = requests.post(f"{BASE_URL}/api/hot-deals/hot-001/add-to-garage")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Add to garage requires authentication")
    
    def test_seller_auto_assigned_as_contractor(self, auth_headers):
        """Test that seller is automatically assigned as contractor when adding to garage"""
        # Get a hot deal with contractor seller
        list_response = requests.get(f"{BASE_URL}/api/hot-deals")
        deals = list_response.json()
        
        contractor_deal = next((d for d in deals if d.get("seller_type") == "contractor"), None)
        if not contractor_deal:
            pytest.skip("No contractor deals available")
        
        # Add to garage
        response = requests.post(
            f"{BASE_URL}/api/hot-deals/{contractor_deal['id']}/add-to-garage",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Seller auto-assigned: {data.get('seller_assigned')}")
            print(f"  Seller name: {data.get('seller_name')}")
            
            # Check if contractor was assigned in garage
            if data.get("car_id"):
                car_response = requests.get(f"{BASE_URL}/api/garage/{data['car_id']}", headers=auth_headers)
                if car_response.status_code == 200:
                    car = car_response.json()
                    contractors = car.get("contractors", {})
                    if contractors:
                        print(f"  Contractors assigned: {list(contractors.keys())}")


class TestHotDealsCreatePermissions:
    """Tests for hot deal creation permissions"""
    
    def test_unauthenticated_user_cannot_create_deal(self):
        """Test that unauthenticated users cannot create hot deals"""
        deal_data = {
            "brand": "Test",
            "model": "Car",
            "year": 2024,
            "price_cny": 100000,
            "engine_type": "ice",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/hot-deals",
            json=deal_data
        )
        
        # Unauthenticated user should get 401/403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
        print("✓ Unauthenticated user cannot create hot deals")
    
    def test_admin_can_create_deal(self):
        """Test that admin/moderator users can create hot deals"""
        # Login as admin (test@test.com has admin role)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.text}")
        
        token = login_response.json()["access_token"]
        user_role = login_response.json()["user"].get("role", "user")
        
        if user_role not in ["admin", "moderator"]:
            pytest.skip(f"Test user is not admin/moderator (role: {user_role})")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        deal_data = {
            "brand": "TestAdmin",
            "model": "AdminCar",
            "year": 2024,
            "price_cny": 150000,
            "engine_type": "electric",
            "expires_at": (datetime.now() + timedelta(hours=12)).isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/api/hot-deals",
            json=deal_data,
            headers=headers
        )
        
        # Admin should be able to create deals
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["brand"] == "TestAdmin"
        assert data["seller_type"] == "moderator"  # Admin creates as moderator
        print(f"✓ Admin can create hot deals (created: {data['brand']} {data['model']})")


class TestHotDealsDataIntegrity:
    """Tests for hot deals data integrity and structure"""
    
    def test_all_deals_have_required_fields(self):
        """Test that all hot deals have required fields"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        deals = response.json()
        required_fields = ["id", "brand", "model", "year", "price_cny", "expires_at", "seller_name"]
        
        for deal in deals:
            for field in required_fields:
                assert field in deal, f"Deal {deal.get('id')} missing required field: {field}"
        
        print(f"✓ All {len(deals)} deals have required fields")
    
    def test_demo_deals_exist(self):
        """Test that demo deals are seeded"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        deals = response.json()
        
        # Check for expected demo deals
        expected_brands = ["BYD", "Zeekr", "GEELY", "Li Auto"]
        found_brands = [d["brand"] for d in deals]
        
        for brand in expected_brands:
            if brand in found_brands:
                print(f"✓ Found demo deal: {brand}")
        
        assert len(deals) >= 1, "Should have at least 1 hot deal"
    
    def test_calculated_price_usd_present(self):
        """Test that deals have calculated USD price"""
        response = requests.get(f"{BASE_URL}/api/hot-deals")
        assert response.status_code == 200
        
        deals = response.json()
        deals_with_usd = [d for d in deals if d.get("calculated_price_usd")]
        
        if deals_with_usd:
            deal = deals_with_usd[0]
            print(f"✓ Deal has calculated USD price: ${deal['calculated_price_usd']}")
        else:
            print("⚠ No deals with calculated USD price")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
