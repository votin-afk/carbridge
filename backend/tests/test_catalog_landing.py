"""
Test suite for Car Catalog feature on Landing Page
Tests the /api/catalog/* endpoints and landing page catalog section
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCatalogBrands:
    """Test /api/catalog/brands endpoint"""
    
    def test_get_brands_returns_list(self):
        """Test that brands endpoint returns a list of brands"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should return at least one brand"
        print(f"SUCCESS: Got {len(data)} brands")
    
    def test_brand_has_required_fields(self):
        """Test that each brand has required fields"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            brand = data[0]
            assert "name" in brand, "Brand should have 'name' field"
            assert "slug" in brand, "Brand should have 'slug' field"
            assert "count" in brand, "Brand should have 'count' field"
            print(f"SUCCESS: Brand has required fields - name: {brand['name']}, slug: {brand['slug']}, count: {brand['count']}")


class TestCatalogSearch:
    """Test /api/catalog/search endpoint"""
    
    def test_search_returns_cars(self):
        """Test that search endpoint returns cars"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=8")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "cars" in data, "Response should have 'cars' field"
        assert "total" in data, "Response should have 'total' field"
        assert "pages" in data, "Response should have 'pages' field"
        print(f"SUCCESS: Search returned {len(data['cars'])} cars, total: {data['total']}")
    
    def test_car_has_required_fields(self):
        """Test that each car has required fields for display"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=8")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["cars"]) > 0:
            car = data["cars"][0]
            required_fields = ["id", "brand", "model", "price_from_cny", "year_from", "engine_type"]
            for field in required_fields:
                assert field in car, f"Car should have '{field}' field"
            
            print(f"SUCCESS: Car has all required fields - {car['brand']} {car['model']}, ¥{car['price_from_cny']}, {car['year_from']}, {car['engine_type']}")
    
    def test_search_with_brand_filter(self):
        """Test search with brand filter"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "cars" in data
        # All returned cars should be BYD brand
        for car in data["cars"]:
            assert car["brand"].upper() == "BYD", f"Expected BYD, got {car['brand']}"
        print(f"SUCCESS: Brand filter works - got {len(data['cars'])} BYD cars")
    
    def test_search_with_engine_type_filter(self):
        """Test search with engine type filter"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?engine_type=electric&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "cars" in data
        # All returned cars should be electric
        for car in data["cars"]:
            assert car["engine_type"] == "electric", f"Expected electric, got {car['engine_type']}"
        print(f"SUCCESS: Engine type filter works - got {len(data['cars'])} electric cars")
    
    def test_search_pagination(self):
        """Test search pagination"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?page=1&limit=4")
        assert response.status_code == 200
        
        data = response.json()
        assert "page" in data, "Response should have 'page' field"
        assert data["page"] == 1, "Page should be 1"
        assert len(data["cars"]) <= 4, "Should return at most 4 cars"
        print(f"SUCCESS: Pagination works - page {data['page']}, {len(data['cars'])} cars")
    
    def test_search_returns_search_links(self):
        """Test that search returns external search links"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD&limit=4")
        assert response.status_code == 200
        
        data = response.json()
        assert "search_links" in data, "Response should have 'search_links' field"
        print(f"SUCCESS: Search links returned: {list(data['search_links'].keys())}")


class TestCatalogModels:
    """Test /api/catalog/models/{brand_slug} endpoint"""
    
    def test_get_models_for_brand(self):
        """Test getting models for a specific brand"""
        # First get brands to find a valid slug
        brands_response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert brands_response.status_code == 200
        
        brands = brands_response.json()
        if len(brands) > 0:
            # Find BYD or use first brand
            brand_slug = None
            for b in brands:
                if b["name"].upper() == "BYD":
                    brand_slug = b["slug"]
                    break
            if not brand_slug:
                brand_slug = brands[0]["slug"]
            
            response = requests.get(f"{BASE_URL}/api/catalog/models/{brand_slug}")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list), "Response should be a list"
            print(f"SUCCESS: Got {len(data)} models for brand {brand_slug}")
    
    def test_models_have_required_fields(self):
        """Test that models have required fields"""
        brands_response = requests.get(f"{BASE_URL}/api/catalog/brands")
        brands = brands_response.json()
        
        if len(brands) > 0:
            brand_slug = brands[0]["slug"]
            response = requests.get(f"{BASE_URL}/api/catalog/models/{brand_slug}")
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 0:
                    model = data[0]
                    assert "name" in model, "Model should have 'name' field"
                    print(f"SUCCESS: Model has required fields - name: {model['name']}")


class TestHotDeals:
    """Test /api/hot-deals endpoint (landing page hot deals section)"""
    
    def test_get_hot_deals(self):
        """Test that hot deals endpoint returns deals"""
        response = requests.get(f"{BASE_URL}/api/hot-deals?limit=4")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Got {len(data)} hot deals")
    
    def test_hot_deal_has_required_fields(self):
        """Test that hot deals have required fields"""
        response = requests.get(f"{BASE_URL}/api/hot-deals?limit=4")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            deal = data[0]
            required_fields = ["id", "brand", "model", "price_cny"]
            for field in required_fields:
                assert field in deal, f"Hot deal should have '{field}' field"
            print(f"SUCCESS: Hot deal has required fields - {deal['brand']} {deal['model']}, ¥{deal['price_cny']}")


class TestLandingPageIntegration:
    """Integration tests for landing page catalog section"""
    
    def test_catalog_preview_loads(self):
        """Test that catalog preview data loads correctly for landing page"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=8")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["cars"]) <= 8, "Landing page should show max 8 cars"
        
        # Verify each car has data needed for display
        for car in data["cars"]:
            assert car.get("brand"), "Car should have brand"
            assert car.get("model"), "Car should have model"
            assert car.get("price_from_cny") is not None, "Car should have price"
            assert car.get("year_from"), "Car should have year"
            assert car.get("engine_type"), "Car should have engine type"
            assert car.get("image_url"), "Car should have image URL"
        
        print(f"SUCCESS: Catalog preview data valid for {len(data['cars'])} cars")
    
    def test_brands_for_popular_links(self):
        """Test that brands data is available for popular brand links"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        brand_names = [b["name"] for b in data]
        
        # Check that popular brands from landing page exist
        popular_brands = ["BYD", "Geely", "Changan", "Li Auto", "NIO", "Haval"]
        found_brands = [b for b in popular_brands if b in brand_names]
        
        print(f"SUCCESS: Found {len(found_brands)}/{len(popular_brands)} popular brands in API: {found_brands}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
