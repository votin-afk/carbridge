"""
Test suite for Che168 API Integration
Tests the catalog endpoints that fetch real data from che168.com via auto-api.com
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestChe168CatalogSearch:
    """Tests for /api/catalog/search endpoint with Che168 data"""
    
    def test_catalog_search_returns_data(self):
        """Test that catalog search returns cars from Che168"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        assert "cars" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        # Should have cars
        assert len(data["cars"]) > 0
        
    def test_catalog_search_returns_che168_source(self):
        """Test that cars have source='che168'"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        cars = data["cars"]
        
        # At least some cars should have che168 source
        che168_cars = [c for c in cars if c.get("source") == "che168"]
        assert len(che168_cars) > 0, "No cars with source='che168' found"
        
    def test_catalog_search_has_required_fields(self):
        """Test that cars have all required fields from Che168 API"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        car = data["cars"][0]
        
        # Required fields
        required_fields = [
            "id", "brand", "model", "year_from", "price_from_cny",
            "engine_type", "body_type", "image_url", "source"
        ]
        for field in required_fields:
            assert field in car, f"Missing required field: {field}"
            
        # Che168 specific fields
        che168_fields = ["mileage", "source_url", "color", "address"]
        for field in che168_fields:
            assert field in car, f"Missing Che168 field: {field}"
            
    def test_catalog_search_price_is_numeric(self):
        """Test that price_from_cny is a valid number"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"]:
            price = car.get("price_from_cny")
            assert price is not None, "price_from_cny should not be None"
            assert isinstance(price, (int, float)), f"price_from_cny should be numeric, got {type(price)}"
            assert price >= 0, "price_from_cny should be non-negative"
            
    def test_catalog_search_mileage_is_numeric_or_none(self):
        """Test that mileage is a valid number or None"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"]:
            mileage = car.get("mileage")
            if mileage is not None:
                assert isinstance(mileage, (int, float)), f"mileage should be numeric, got {type(mileage)}"
                assert mileage >= 0, "mileage should be non-negative"
                
    def test_catalog_search_year_is_valid(self):
        """Test that year_from is a valid year"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"]:
            year = car.get("year_from")
            assert year is not None, "year_from should not be None"
            assert isinstance(year, int), f"year_from should be int, got {type(year)}"
            assert 1990 <= year <= 2030, f"year_from {year} is out of valid range"
            
    def test_catalog_search_source_url_is_valid(self):
        """Test that source_url is a valid che168 URL"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"]:
            if car.get("source") == "che168":
                source_url = car.get("source_url")
                if source_url:
                    assert "che168.com" in source_url, f"source_url should contain che168.com: {source_url}"


class TestChe168BrandFilter:
    """Tests for brand filtering with Che168 data"""
    
    def test_search_by_brand_byd(self):
        """Test searching for BYD brand returns BYD cars"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["cars"]) > 0, "Should return BYD cars"
        
        for car in data["cars"]:
            assert car["brand"].upper() == "BYD", f"Expected BYD, got {car['brand']}"
            
    def test_search_by_brand_geely(self):
        """Test searching for Geely brand"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=Geely")
        assert response.status_code == 200
        
        data = response.json()
        # May or may not have results depending on API data
        if data["cars"]:
            for car in data["cars"]:
                assert car["brand"].lower() == "geely", f"Expected Geely, got {car['brand']}"


class TestChe168Brands:
    """Tests for /api/catalog/brands endpoint"""
    
    def test_brands_returns_list(self):
        """Test that brands endpoint returns a list"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Brands should be a list"
        assert len(data) > 0, "Should have at least one brand"
        
    def test_brands_have_required_fields(self):
        """Test that each brand has required fields"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        for brand in data[:10]:  # Check first 10 brands
            assert "name" in brand, "Brand should have name"
            assert "slug" in brand, "Brand should have slug"
            
    def test_brands_include_popular_brands(self):
        """Test that popular Chinese brands are included"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        brand_names = [b["name"].lower() for b in data]
        
        # Check for some popular brands
        popular_brands = ["byd", "geely", "changan", "haval"]
        found_brands = [b for b in popular_brands if b in brand_names]
        assert len(found_brands) >= 2, f"Should include popular brands, found: {found_brands}"


class TestChe168Models:
    """Tests for /api/catalog/models/{brand} endpoint"""
    
    def test_models_for_byd(self):
        """Test getting models for BYD brand"""
        response = requests.get(f"{BASE_URL}/api/catalog/models/BYD")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Models should be a list"
        assert len(data) > 0, "BYD should have models"
        
    def test_models_have_required_fields(self):
        """Test that each model has required fields"""
        response = requests.get(f"{BASE_URL}/api/catalog/models/BYD")
        assert response.status_code == 200
        
        data = response.json()
        for model in data[:5]:  # Check first 5 models
            assert "name" in model, "Model should have name"
            assert "slug" in model, "Model should have slug"
            
    def test_models_for_unknown_brand(self):
        """Test getting models for unknown brand returns empty list"""
        response = requests.get(f"{BASE_URL}/api/catalog/models/UnknownBrand123")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        # May be empty for unknown brand


class TestChe168DataQuality:
    """Tests for data quality from Che168 API"""
    
    def test_image_urls_are_valid(self):
        """Test that image URLs are valid HTTP URLs"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"][:5]:  # Check first 5 cars
            image_url = car.get("image_url")
            assert image_url is not None, "image_url should not be None"
            assert image_url.startswith("http"), f"image_url should be HTTP URL: {image_url}"
            
    def test_engine_type_is_valid(self):
        """Test that engine_type is one of valid values"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        valid_engine_types = ["ice", "electric", "hybrid"]
        
        for car in data["cars"]:
            engine_type = car.get("engine_type")
            assert engine_type in valid_engine_types, f"Invalid engine_type: {engine_type}"
            
    def test_body_type_is_valid(self):
        """Test that body_type is one of valid values"""
        response = requests.get(f"{BASE_URL}/api/catalog/search")
        assert response.status_code == 200
        
        data = response.json()
        valid_body_types = ["sedan", "suv", "hatchback", "mpv", "wagon", "pickup", "coupe"]
        
        for car in data["cars"]:
            body_type = car.get("body_type")
            assert body_type in valid_body_types, f"Invalid body_type: {body_type}"


class TestChe168Pagination:
    """Tests for pagination with Che168 data"""
    
    def test_pagination_page_1(self):
        """Test first page of results"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?page=1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert len(data["cars"]) > 0
        
    def test_pagination_page_2(self):
        """Test second page of results"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?page=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 2
        # May or may not have cars on page 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
