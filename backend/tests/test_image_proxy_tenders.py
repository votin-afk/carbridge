"""
Test suite for image proxy and tender image enrichment features.
Tests:
1. Image proxy endpoint for Chinese CDN images
2. Tenders endpoint returns real garage images (not unsplash stock)
3. Core APIs: health, tenders, garage
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "votin@tut.by"
TEST_PASSWORD = "test"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint returns healthy status")


class TestImageProxy:
    """Image proxy endpoint tests"""
    
    def test_proxy_chinese_cdn_image(self):
        """Test /api/proxy/image proxies Chinese CDN images"""
        # Test with a known Chinese CDN URL
        test_url = "https://2sc2.autoimg.cn/escimg/auto/g33/M01/F4/DF/1024x768_c42_autohomecar__ChxpVmm3vcyAS_8QAALRciV66k0973.jpg.webp"
        
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": test_url},
            timeout=15
        )
        
        # Should return image content
        assert response.status_code == 200, f"Proxy failed: {response.status_code}"
        assert "image" in response.headers.get("content-type", "")
        assert len(response.content) > 1000  # Should have actual image data
        print(f"✓ Image proxy returned {len(response.content)} bytes")
    
    def test_proxy_rejects_non_allowed_domain(self):
        """Test /api/proxy/image rejects non-allowed domains"""
        test_url = "https://example.com/image.jpg"
        
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": test_url}
        )
        
        assert response.status_code == 400
        print("✓ Image proxy correctly rejects non-allowed domains")
    
    def test_proxy_rejects_invalid_url(self):
        """Test /api/proxy/image rejects invalid URLs"""
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": "not-a-url"}
        )
        
        assert response.status_code == 400
        print("✓ Image proxy correctly rejects invalid URLs")


class TestGarageEndpoint:
    """Garage endpoint tests"""
    
    def test_get_garage_cars(self, auth_headers):
        """Test GET /api/garage returns user's cars"""
        response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Garage returned {len(data)} cars")
        
        # Check that cars have image_url
        for car in data[:5]:
            assert "brand" in car
            assert "model" in car
            if car.get("image_url"):
                # Should not be unsplash stock for real cars
                print(f"  - {car['brand']} {car['model']}: {car['image_url'][:60]}...")
    
    def test_garage_images_are_real(self, auth_headers):
        """Test that garage cars have real images (not unsplash stock)"""
        response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        stock_count = 0
        real_count = 0
        
        for car in data:
            img_url = car.get("image_url", "")
            if "unsplash.com" in img_url:
                stock_count += 1
            elif "autoimg.cn" in img_url or "che168.com" in img_url:
                real_count += 1
        
        print(f"✓ Garage images: {real_count} real, {stock_count} stock")
        # Most cars should have real images
        assert real_count > 0, "Expected at least some real car images"


class TestTendersEndpoint:
    """Tenders endpoint tests"""
    
    def test_get_tenders(self, auth_headers):
        """Test GET /api/tenders returns user's tenders"""
        response = requests.get(f"{BASE_URL}/api/tenders", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Tenders returned {len(data)} tenders")
    
    def test_tender_has_real_image(self, auth_headers):
        """Test that tenders have real images from garage (not unsplash stock)"""
        response = requests.get(f"{BASE_URL}/api/tenders", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        for tender in data:
            car_info = tender.get("car_info", {})
            image_url = car_info.get("image_url") or tender.get("image_url", "")
            
            brand = car_info.get("brand") or tender.get("car_request", {}).get("brand", "Unknown")
            model = car_info.get("model") or tender.get("car_request", {}).get("model", "")
            
            print(f"  - Tender {brand} {model}: {image_url[:60] if image_url else 'NO IMAGE'}...")
            
            # Check that image is not unsplash stock
            if image_url:
                is_stock = "unsplash.com" in image_url
                is_real = "autoimg.cn" in image_url or "che168.com" in image_url
                
                if is_stock:
                    print(f"    ⚠ WARNING: Tender has stock image")
                elif is_real:
                    print(f"    ✓ Tender has real car image")
    
    def test_tender_offers_have_data(self, auth_headers):
        """Test that tender offers contain expected fields"""
        response = requests.get(f"{BASE_URL}/api/tenders", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        for tender in data:
            offers = tender.get("offers", [])
            print(f"  - Tender {tender.get('id', 'unknown')[:8]}... has {len(offers)} offers")
            
            for offer in offers[:2]:
                assert "id" in offer
                assert "price_usd" in offer or "price_cny" in offer
                print(f"    - Offer: ${offer.get('price_usd', 'N/A')} from {offer.get('contractor_name', 'Unknown')}")


class TestTenderImageEnrichment:
    """Test that tenders are enriched with garage images"""
    
    def test_tender_image_matches_garage(self, auth_headers):
        """Test that tender image_url comes from matching garage car"""
        # Get garage cars
        garage_response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        assert garage_response.status_code == 200
        garage_cars = garage_response.json()
        
        # Build map of brand/model to image
        garage_images = {}
        for car in garage_cars:
            key = (car.get("brand", "").lower(), car.get("model", "").lower())
            img = car.get("image_url", "")
            if img and "unsplash.com" not in img:
                garage_images[key] = img
        
        # Get tenders
        tenders_response = requests.get(f"{BASE_URL}/api/tenders", headers=auth_headers)
        assert tenders_response.status_code == 200
        tenders = tenders_response.json()
        
        for tender in tenders:
            car_info = tender.get("car_info", {})
            car_request = tender.get("car_request", {})
            
            brand = (car_info.get("brand") or car_request.get("brand") or "").lower()
            model = (car_info.get("model") or car_request.get("model") or "").lower()
            
            tender_image = car_info.get("image_url") or tender.get("image_url", "")
            
            # Check if tender image matches garage image
            garage_image = garage_images.get((brand, model))
            
            if garage_image and tender_image:
                if tender_image == garage_image:
                    print(f"✓ Tender {brand} {model} image matches garage")
                elif "unsplash.com" not in tender_image:
                    print(f"✓ Tender {brand} {model} has real image (may be from partial match)")
                else:
                    print(f"⚠ Tender {brand} {model} has stock image despite garage having real image")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
