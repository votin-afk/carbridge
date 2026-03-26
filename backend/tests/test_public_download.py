"""
Test suite for /api/files/{file_id}/public-download endpoint
Tests file downloading with JWT token as query parameter for:
- Regular users (deal owners)
- Admin/Moderator users
- Contractor users
- Invalid/missing tokens
- Non-existent files
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"
USER_EMAIL = "test@test.com"
USER_PASSWORD = "test"
CONTRACTOR_EMAIL = "test.contractor@test.com"
CONTRACTOR_PASSWORD = "test123"

# Known file IDs from context
KNOWN_FILE_IDS = [
    "db8f4250-6f00-4592-8bee-bc618970753a",  # deal 79622ded
    "4faaa7c5-6d72-4c36-9eb0-282701e0b638",  # deal ed873a26
    "3b4c7c01-db45-4039-b8dc-e06093603664",  # deal fec82ca8
]


class TestPublicDownloadEndpoint:
    """Tests for GET /api/files/{file_id}/public-download?token=JWT"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get regular user JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"User login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor JWT token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Contractor login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def existing_file_id(self, admin_token):
        """Find an existing file ID from deals"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to get deals and find a file
        response = requests.get(f"{BASE_URL}/api/moderator/deals", headers=headers)
        if response.status_code == 200:
            deals = response.json()
            for deal in deals:
                deal_id = deal.get("id")
                if deal_id:
                    files_response = requests.get(
                        f"{BASE_URL}/api/moderator/deals/{deal_id}/files",
                        headers=headers
                    )
                    if files_response.status_code == 200:
                        files = files_response.json()
                        if files:
                            return files[0].get("id"), deal_id
        
        # Try known file IDs
        for file_id in KNOWN_FILE_IDS:
            response = requests.get(
                f"{BASE_URL}/api/files/{file_id}/public-download",
                params={"token": admin_token}
            )
            if response.status_code == 200:
                return file_id, None
        
        pytest.skip("No existing files found for testing")
    
    # ==================== TESTS WITHOUT TOKEN ====================
    
    def test_download_without_token_returns_401(self):
        """Test that downloading without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/files/any-file-id/public-download")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Download without token returns 401: {response.json()}")
    
    def test_download_with_empty_token_returns_401(self):
        """Test that downloading with empty token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/files/any-file-id/public-download",
            params={"token": ""}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Download with empty token returns 401")
    
    # ==================== TESTS WITH INVALID TOKEN ====================
    
    def test_download_with_invalid_token_returns_401(self):
        """Test that downloading with invalid token returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/files/any-file-id/public-download",
            params={"token": "invalid-jwt-token"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Download with invalid token returns 401: {response.json()}")
    
    def test_download_with_malformed_jwt_returns_401(self):
        """Test that downloading with malformed JWT returns 401"""
        response = requests.get(
            f"{BASE_URL}/api/files/any-file-id/public-download",
            params={"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Download with malformed JWT returns 401")
    
    # ==================== TESTS WITH NON-EXISTENT FILE ====================
    
    def test_download_nonexistent_file_with_valid_token_returns_404(self, admin_token):
        """Test that downloading non-existent file returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/files/nonexistent-file-id-12345/public-download",
            params={"token": admin_token}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Download non-existent file returns 404: {response.json()}")
    
    # ==================== TESTS WITH VALID ADMIN TOKEN ====================
    
    def test_download_with_admin_token_returns_file(self, admin_token, existing_file_id):
        """Test that admin can download file with valid token"""
        file_id, deal_id = existing_file_id
        response = requests.get(
            f"{BASE_URL}/api/files/{file_id}/public-download",
            params={"token": admin_token}
        )
        
        # Should return 200 with file content
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        # Check content-type header exists
        content_type = response.headers.get("content-type", "")
        assert content_type, "Content-Type header should be present"
        
        # Check content-disposition header for filename
        content_disp = response.headers.get("content-disposition", "")
        
        print(f"✓ Admin download successful: status={response.status_code}, content-type={content_type}, size={len(response.content)} bytes")
    
    # ==================== TESTS WITH VALID USER TOKEN ====================
    
    def test_download_with_user_token_access_check(self, user_token, existing_file_id):
        """Test user token access - may return 200 (if owner) or 403 (if not owner)"""
        file_id, deal_id = existing_file_id
        response = requests.get(
            f"{BASE_URL}/api/files/{file_id}/public-download",
            params={"token": user_token}
        )
        
        # User should get 200 if owner, 403 if not owner
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}"
        
        if response.status_code == 200:
            print(f"✓ User is owner - download successful: size={len(response.content)} bytes")
        else:
            print(f"✓ User is not owner - access denied (403)")
    
    # ==================== TESTS WITH CONTRACTOR TOKEN ====================
    
    def test_download_with_contractor_token_access_check(self, contractor_token, existing_file_id):
        """Test contractor token access - may return 200 (if assigned) or 403 (if not assigned)"""
        file_id, deal_id = existing_file_id
        response = requests.get(
            f"{BASE_URL}/api/files/{file_id}/public-download",
            params={"token": contractor_token}
        )
        
        # Contractor should get 200 if assigned to deal stage, 403 if not
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}"
        
        if response.status_code == 200:
            print(f"✓ Contractor is assigned - download successful: size={len(response.content)} bytes")
        else:
            print(f"✓ Contractor is not assigned - access denied (403)")
    
    # ==================== URL ENCODING TEST ====================
    
    def test_token_url_encoding(self, admin_token, existing_file_id):
        """Test that URL-encoded token works correctly"""
        import urllib.parse
        file_id, deal_id = existing_file_id
        
        # URL encode the token
        encoded_token = urllib.parse.quote(admin_token, safe='')
        
        response = requests.get(
            f"{BASE_URL}/api/files/{file_id}/public-download?token={encoded_token}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ URL-encoded token works correctly")


class TestFrontendDownloadIntegration:
    """Tests to verify frontend download URLs are correctly formed"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_frontend_download_url_format(self, admin_token):
        """Test that the frontend download URL format works"""
        # This simulates what the frontend does:
        # const url = `${API}/files/${fileId}/public-download?token=${encodeURIComponent(token)}`;
        # window.open(url, '_blank');
        
        import urllib.parse
        
        # Get a file to test with
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/moderator/deals", headers=headers)
        
        if response.status_code != 200:
            pytest.skip("Could not get deals")
        
        deals = response.json()
        file_id = None
        
        for deal in deals:
            deal_id = deal.get("id")
            if deal_id:
                files_response = requests.get(
                    f"{BASE_URL}/api/moderator/deals/{deal_id}/files",
                    headers=headers
                )
                if files_response.status_code == 200:
                    files = files_response.json()
                    if files:
                        file_id = files[0].get("id")
                        break
        
        if not file_id:
            pytest.skip("No files found")
        
        # Construct URL exactly as frontend does
        encoded_token = urllib.parse.quote(admin_token, safe='')
        url = f"{BASE_URL}/api/files/{file_id}/public-download?token={encoded_token}"
        
        # Make request
        response = requests.get(url)
        
        assert response.status_code == 200, f"Frontend URL format failed: {response.status_code}"
        print(f"✓ Frontend download URL format works correctly")
        print(f"  URL pattern: /api/files/{{file_id}}/public-download?token={{encoded_token}}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
