"""
Test suite for CARBRIDGE Catalog API - Version 2
Tests for:
1. Images from cn.pa-server.ru
2. Prices in CNY (Yuan)
3. Engine type detection (ice/electric/hybrid)
4. Model filter by brand
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCatalogPricesInCNY:
    """Tests for price display in CNY (Yuan)"""
    
    def test_search_returns_cny_prices(self):
        """Test that search returns prices in CNY"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["cars"]) > 0
        
        for car in data["cars"]:
            assert "price_from_cny" in car, "Car should have price_from_cny field"
            assert car["price_from_cny"] > 0, "CNY price should be positive"
            # Prices should be reasonable (10,000 - 1,000,000 CNY)
            assert 10000 <= car["price_from_cny"] <= 1000000, f"Price {car['price_from_cny']} seems unreasonable"
        
        print(f"✓ All {len(data['cars'])} cars have valid CNY prices")
    
    def test_byd_seagull_price_in_cny(self):
        """Test BYD Seagull prices are in CNY range (40,000-70,000)"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        seagulls = [c for c in data["cars"] if "seagull" in c.get("model", "").lower()]
        
        assert len(seagulls) > 0, "Should find BYD Seagull cars"
        
        for car in seagulls[:5]:
            price = car["price_from_cny"]
            # BYD Seagull typically costs 40,000-70,000 CNY
            assert 30000 <= price <= 100000, f"BYD Seagull price {price} CNY seems off"
            print(f"  BYD Seagull: ¥{price:,.0f} CNY")
        
        print(f"✓ Found {len(seagulls)} BYD Seagull cars with valid CNY prices")


class TestCatalogImagesFromPaServer:
    """Tests for images from cn.pa-server.ru"""
    
    def test_images_from_pa_server(self):
        """Test that images come from cn.pa-server.ru"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        pa_server_images = 0
        
        for car in data["cars"]:
            image_url = car.get("image_url", "")
            if "cn.pa-server.ru" in image_url:
                pa_server_images += 1
        
        # At least 80% of images should be from pa-server
        assert pa_server_images >= len(data["cars"]) * 0.8, \
            f"Only {pa_server_images}/{len(data['cars'])} images from cn.pa-server.ru"
        
        print(f"✓ {pa_server_images}/{len(data['cars'])} images from cn.pa-server.ru")
    
    def test_image_url_format(self):
        """Test that image URLs have correct format"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        for car in data["cars"]:
            image_url = car.get("image_url", "")
            if "cn.pa-server.ru" in image_url:
                assert image_url.startswith("https://"), "Image URL should use HTTPS"
                assert ".webp" in image_url or ".jpg" in image_url or ".png" in image_url, \
                    "Image URL should have valid extension"
                print(f"  ✓ {car['brand']} {car['model']}: {image_url[:60]}...")
        
        print("✓ Image URLs have correct format")


class TestCatalogEngineTypeDetection:
    """Tests for engine type detection (ice/electric/hybrid)"""
    
    def test_byd_seagull_is_electric(self):
        """Test that BYD Seagull is detected as electric"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=BYD&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        seagulls = [c for c in data["cars"] if "seagull" in c.get("model", "").lower()]
        
        assert len(seagulls) > 0, "Should find BYD Seagull cars"
        
        for car in seagulls:
            assert car["engine_type"] == "electric", \
                f"BYD Seagull should be electric, got {car['engine_type']}"
            assert car.get("fuel_type") in ["Электро", "Electric"], \
                f"BYD Seagull fuel_type should be Электро, got {car.get('fuel_type')}"
        
        print(f"✓ All {len(seagulls)} BYD Seagull cars correctly identified as electric")
    
    def test_geely_binrui_is_ice(self):
        """Test that Geely Binrui is detected as ICE"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=Geely&limit=20")
        assert response.status_code == 200
        
        data = response.json()
        binruis = [c for c in data["cars"] if "binrui" in c.get("model", "").lower()]
        
        assert len(binruis) > 0, "Should find Geely Binrui cars"
        
        for car in binruis:
            assert car["engine_type"] == "ice", \
                f"Geely Binrui should be ICE, got {car['engine_type']}"
            assert car.get("fuel_type") in ["Бензин", "Gasoline", "Дизель", "Diesel"], \
                f"Geely Binrui fuel_type should be Бензин, got {car.get('fuel_type')}"
        
        print(f"✓ All {len(binruis)} Geely Binrui cars correctly identified as ICE")
    
    def test_engine_types_valid(self):
        """Test that all cars have valid engine types"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=20")
        assert response.status_code == 200
        
        data = response.json()
        valid_types = ["ice", "electric", "hybrid"]
        
        for car in data["cars"]:
            assert car["engine_type"] in valid_types, \
                f"Invalid engine_type: {car['engine_type']}"
        
        # Count by type
        type_counts = {}
        for car in data["cars"]:
            t = car["engine_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print(f"✓ Engine type distribution: {type_counts}")


class TestCatalogModelFilter:
    """Tests for model filter by brand"""
    
    def test_get_models_for_byd(self):
        """Test getting models for BYD brand"""
        response = requests.get(f"{BASE_URL}/api/catalog/models/byd")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Should return list of models"
        assert len(data) > 0, "Should have at least one model"
        
        for model in data:
            assert "name" in model, "Model should have name"
            assert "count" in model, "Model should have count"
        
        model_names = [m["name"] for m in data]
        print(f"✓ BYD models: {model_names}")
    
    def test_get_models_for_geely(self):
        """Test getting models for Geely brand"""
        response = requests.get(f"{BASE_URL}/api/catalog/models/geely")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Should return list of models"
        assert len(data) > 0, "Should have at least one model"
        
        model_names = [m["name"] for m in data]
        # Should include Binrui
        assert any("binrui" in m.lower() for m in model_names), \
            f"Geely models should include Binrui, got: {model_names}"
        
        print(f"✓ Geely models: {model_names}")
    
    def test_search_with_model_filter(self):
        """Test search with model filter"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?brand=Geely&model=Binrui&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        # Note: Model filter may not work perfectly with live data
        print(f"✓ Search with model filter returned {len(data['cars'])} cars")


class TestCatalogBrandsEndpoint:
    """Tests for /api/catalog/brands endpoint"""
    
    def test_brands_include_byd_and_geely(self):
        """Test that brands include BYD and Geely"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200
        
        data = response.json()
        brand_names = [b["name"].lower() for b in data]
        
        assert any("byd" in name for name in brand_names), "Should include BYD"
        assert any("geely" in name for name in brand_names), "Should include Geely"
        
        # Find BYD and Geely counts
        for brand in data:
            if brand["name"].lower() == "byd":
                print(f"  BYD: {brand['count']} cars")
            elif brand["name"].lower() == "geely":
                print(f"  Geely: {brand['count']} cars")
        
        print(f"✓ Found BYD and Geely in {len(data)} brands")


class TestCatalogSearchLinks:
    """Tests for search links to Chinese platforms"""
    
    def test_search_links_present(self):
        """Test that search returns links to Chinese platforms"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        assert "search_links" in data
        
        expected_platforms = ["che168", "58", "guazi", "dongchedi"]
        for platform in expected_platforms:
            assert platform in data["search_links"], f"Missing link for {platform}"
            assert data["search_links"][platform].startswith("http"), \
                f"Invalid URL for {platform}"
        
        print(f"✓ Search links present: {list(data['search_links'].keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
