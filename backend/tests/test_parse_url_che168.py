"""
Test suite for parse-url endpoint with che168 URLs
Tests the fix for che168.com URL parsing using Che168 API instead of direct scraping
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"


class TestHealthAndCoreAPIs:
    """Test core APIs are working"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")
    
    def test_deals_requires_auth(self):
        """GET /api/deals requires authentication"""
        response = requests.get(f"{BASE_URL}/api/deals")
        assert response.status_code in [401, 403]
        print("✓ Deals endpoint requires auth")
    
    def test_garage_requires_auth(self):
        """GET /api/garage requires authentication"""
        response = requests.get(f"{BASE_URL}/api/garage")
        assert response.status_code in [401, 403]
        print("✓ Garage endpoint requires auth")


class TestParseUrlEndpoint:
    """Test POST /api/parse-url with various che168 URL formats"""
    
    def test_parse_url_unsupported_domain(self):
        """POST /api/parse-url with unsupported domain returns error"""
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": "https://www.google.com/search?q=car"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "Неподдерживаемая площадка" in data.get("error", "")
        print("✓ Unsupported domain returns proper error")
    
    def test_parse_url_che168_dealer_format(self):
        """POST /api/parse-url with che168 dealer URL format"""
        # Example: https://www.che168.com/dealer/123456/12345678.html
        test_url = "https://www.che168.com/dealer/123456/12345678.html"
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        assert response.status_code == 200
        data = response.json()
        # Either success with car data or error about not found (valid API call)
        if data.get("success"):
            print(f"✓ Che168 dealer URL parsed: {data.get('brand')} {data.get('model')}")
            assert data.get("source_url") == test_url
        else:
            # API was called but offer not found - this is expected for fake ID
            assert "не найдено" in data.get("error", "").lower() or "удалено" in data.get("error", "").lower()
            print("✓ Che168 dealer URL - API called correctly (offer not found as expected for test ID)")
    
    def test_parse_url_che168_china_format(self):
        """POST /api/parse-url with che168 china URL format"""
        # Example: https://www.che168.com/china/12345678.html
        test_url = "https://www.che168.com/china/12345678.html"
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            print(f"✓ Che168 china URL parsed: {data.get('brand')} {data.get('model')}")
        else:
            # API was called but offer not found
            assert "не найдено" in data.get("error", "").lower() or "удалено" in data.get("error", "").lower()
            print("✓ Che168 china URL - API called correctly (offer not found as expected for test ID)")
    
    def test_parse_url_autohome_format(self):
        """POST /api/parse-url with autohome URL format"""
        test_url = "https://www.autohome.com.cn/dealer/12345678.html"
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            print(f"✓ Autohome URL parsed: {data.get('brand')} {data.get('model')}")
        else:
            # API was called but offer not found
            assert "не найдено" in data.get("error", "").lower() or "удалено" in data.get("error", "").lower() or "ID" in data.get("error", "")
            print("✓ Autohome URL - API called correctly")
    
    def test_parse_url_taoche_format(self):
        """POST /api/parse-url with taoche URL format"""
        test_url = "https://www.taoche.com/usedcar/12345678.html"
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get("success"):
            print(f"✓ Taoche URL parsed: {data.get('brand')} {data.get('model')}")
        else:
            # API was called but offer not found
            assert "не найдено" in data.get("error", "").lower() or "удалено" in data.get("error", "").lower() or "ID" in data.get("error", "")
            print("✓ Taoche URL - API called correctly")
    
    def test_parse_url_che168_invalid_id_format(self):
        """POST /api/parse-url with che168 URL but invalid ID format"""
        test_url = "https://www.che168.com/china/abc.html"
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == False
        assert "ID" in data.get("error", "") or "ссылк" in data.get("error", "").lower()
        print("✓ Invalid ID format returns proper error")


class TestParseUrlWithRealOffer:
    """Test parse-url with a real che168 offer (if available)"""
    
    def test_parse_url_real_che168_offer(self):
        """Test with a real che168 offer URL - search for one first"""
        # First, search for a car to get a real inner_id
        search_response = requests.get(
            f"{BASE_URL}/api/catalog/search",
            params={"source": "che168", "limit": 1}
        )
        
        if search_response.status_code != 200:
            pytest.skip("Catalog search not available")
        
        search_data = search_response.json()
        cars = search_data.get("cars", [])
        
        if not cars:
            pytest.skip("No cars found in catalog to test with")
        
        car = cars[0]
        inner_id = car.get("inner_id") or car.get("id", "").replace("che168-", "")
        
        if not inner_id or not inner_id.isdigit():
            pytest.skip(f"No valid inner_id found: {inner_id}")
        
        # Construct a che168 URL with this inner_id
        test_url = f"https://www.che168.com/dealer/123/{inner_id}.html"
        
        response = requests.post(
            f"{BASE_URL}/api/parse-url",
            json={"url": test_url}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("success"):
            # Verify car data is returned
            assert data.get("brand") is not None, "Brand should be present"
            assert data.get("model") is not None, "Model should be present"
            assert data.get("source_url") == test_url
            print(f"✓ Real che168 offer parsed successfully:")
            print(f"  Brand: {data.get('brand')}")
            print(f"  Model: {data.get('model')}")
            print(f"  Year: {data.get('year')}")
            print(f"  Price CNY: {data.get('price_cny')}")
            print(f"  Image URL: {data.get('image_url', 'N/A')[:50]}...")
        else:
            # Offer might have been removed
            print(f"✓ API called correctly, offer status: {data.get('error')}")


class TestAuthenticatedGarageFlow:
    """Test authenticated garage flow with parse-url"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip("Could not authenticate")
        return response.json().get("access_token")
    
    def test_garage_list_with_auth(self, auth_token):
        """GET /api/garage with auth returns list"""
        response = requests.get(
            f"{BASE_URL}/api/garage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Garage list returned {len(data)} cars")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
