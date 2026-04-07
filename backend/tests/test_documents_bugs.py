"""
Test suite for Documents section bug fixes:
1. Car images proxy for Chinese URLs
2. File download endpoint
3. Chat endpoint (Che168API import)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com')

# Test credentials
TEST_USER = {"email": "votin@tut.by", "password": "test"}
TEST_DEAL_ID = "c650aaba-5356-4e97-8cee-133e920c3f03"
TEST_FILE_ID = "f29d6f50-e658-4441-a2db-ff9bd4660d57"


class TestImageProxy:
    """Tests for /api/proxy/image endpoint - Chinese CDN image proxying"""
    
    def test_proxy_image_autoimg_cn(self):
        """Test proxying image from autoimg.cn domain"""
        test_url = "https://2sc2.autoimg.cn/escimg/auto/g34/M07/4D/D0/1024x768_c42_autohomecar__ChxpWGjjymyAWS0rAAcF-W8-rEE250.jpg.webp"
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": test_url},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "image" in response.headers.get("content-type", ""), "Response should be an image"
        print(f"SUCCESS: Proxied autoimg.cn image, content-type: {response.headers.get('content-type')}")
    
    def test_proxy_image_rejects_invalid_domain(self):
        """Test that proxy rejects non-allowed domains"""
        test_url = "https://example.com/image.jpg"
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": test_url},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for non-allowed domain, got {response.status_code}"
        print("SUCCESS: Proxy correctly rejects non-allowed domains")
    
    def test_proxy_image_rejects_invalid_url(self):
        """Test that proxy rejects invalid URLs"""
        response = requests.get(
            f"{BASE_URL}/api/proxy/image",
            params={"url": "not-a-valid-url"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for invalid URL, got {response.status_code}"
        print("SUCCESS: Proxy correctly rejects invalid URLs")


class TestFileDownload:
    """Tests for /api/files/{file_id}/public-download endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER,
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_file_download_with_token(self, auth_token):
        """Test file download with valid token"""
        response = requests.get(
            f"{BASE_URL}/api/files/{TEST_FILE_ID}/public-download",
            params={"token": auth_token},
            timeout=30,
            allow_redirects=True
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: File download returned 200, content-length: {response.headers.get('content-length', 'unknown')}")
    
    def test_file_download_without_token(self):
        """Test file download without token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/files/{TEST_FILE_ID}/public-download",
            timeout=10
        )
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        print("SUCCESS: File download correctly requires authentication")
    
    def test_file_download_invalid_file_id(self, auth_token):
        """Test file download with invalid file ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/files/invalid-file-id/public-download",
            params={"token": auth_token},
            timeout=10
        )
        assert response.status_code == 404, f"Expected 404 for invalid file ID, got {response.status_code}"
        print("SUCCESS: File download correctly returns 404 for invalid file ID")


class TestChatEndpoint:
    """Tests for /api/chat endpoint - verifies Che168API import works"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER,
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_chat_endpoint_works(self, auth_token):
        """Test chat endpoint responds without NameError (Che168API import fixed)"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Hello"},
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        print(f"SUCCESS: Chat endpoint works, response: {data['response'][:50]}...")


class TestDealFiles:
    """Tests for deal files endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER,
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_get_deal_files(self, auth_token):
        """Test getting files for a deal"""
        response = requests.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        files = response.json()
        assert isinstance(files, list), "Response should be a list"
        assert len(files) > 0, "Deal should have files"
        
        # Verify file structure
        file = files[0]
        assert "id" in file, "File should have 'id'"
        assert "original_name" in file, "File should have 'original_name'"
        print(f"SUCCESS: Got {len(files)} files for deal")


class TestDealImages:
    """Tests for deal car images using proxy"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER,
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_deal_has_chinese_image_url(self, auth_token):
        """Test that deal with Chinese car has autoimg.cn image URL"""
        response = requests.get(
            f"{BASE_URL}/api/deals",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        deals = response.json()
        
        # Find the iCAR deal
        icar_deal = next((d for d in deals if d.get("id") == TEST_DEAL_ID), None)
        assert icar_deal is not None, f"Deal {TEST_DEAL_ID} not found"
        
        car_info = icar_deal.get("car_info", {})
        image_url = car_info.get("image_url", "")
        
        # Verify it's a Chinese CDN URL
        assert "autoimg.cn" in image_url or "che168.com" in image_url, \
            f"Expected Chinese CDN URL, got: {image_url}"
        print(f"SUCCESS: Deal has Chinese CDN image URL: {image_url[:80]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
