"""
Test suite for Contractor Profile Page feature
Tests:
- GET /api/contractor/profile - Get contractor's own profile
- PUT /api/contractor/profile - Update profile fields
- POST /api/contractor/profile/files - Upload profile files
- DELETE /api/contractor/profile/files/{file_id} - Delete profile file
- GET /api/profile-files/{file_id}/download - Download profile file (public)
- GET /api/contractors/{contractor_id}/page - Get public profile page
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CONTRACTOR_EMAIL = "horon4ik@icloud.com"
CONTRACTOR_PASSWORD = "test123"
CONTRACTOR_ID = "94d357ad-4094-449a-af9e-fcd403105459"

class TestContractorProfileBackend:
    """Test contractor profile backend endpoints"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Login as contractor and get token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        assert response.status_code == 200, f"Contractor login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, contractor_token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {contractor_token}"}
    
    # ---- GET /api/contractor/profile ----
    def test_get_profile_requires_auth(self):
        """GET /api/contractor/profile requires authentication"""
        response = requests.get(f"{BASE_URL}/api/contractor/profile")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_get_profile_returns_data(self, auth_headers):
        """GET /api/contractor/profile returns profile data"""
        response = requests.get(f"{BASE_URL}/api/contractor/profile", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check profile fields exist
        assert "contractor_id" in data or "contractor" in data, "Missing contractor info"
        
        # Check profile fields
        profile_fields = ["about", "slogan", "staff", "certificates", "portfolio_cases", "working_hours"]
        for field in profile_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check files array
        assert "files" in data, "Missing files array"
        assert isinstance(data["files"], list), "files should be a list"
        
        print(f"Profile data keys: {list(data.keys())}")
        print(f"About: {data.get('about', '')[:100]}...")
        print(f"Slogan: {data.get('slogan', '')}")
        print(f"Staff count: {len(data.get('staff', []))}")
        print(f"Certificates count: {len(data.get('certificates', []))}")
        print(f"Portfolio cases count: {len(data.get('portfolio_cases', []))}")
        print(f"Files count: {len(data.get('files', []))}")
    
    def test_get_profile_has_ola_cars_data(self, auth_headers):
        """GET /api/contractor/profile returns OLa CARS pre-filled data"""
        response = requests.get(f"{BASE_URL}/api/contractor/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # OLa CARS should have pre-filled data
        # Check if slogan or about is filled
        has_content = bool(data.get("slogan")) or bool(data.get("about"))
        print(f"Has pre-filled content: {has_content}")
        print(f"Slogan: {data.get('slogan', 'N/A')}")
        print(f"City: {data.get('city', 'N/A')}")
        print(f"Address: {data.get('address', 'N/A')}")
        
        # Check staff
        staff = data.get("staff", [])
        print(f"Staff members: {len(staff)}")
        for s in staff[:3]:
            print(f"  - {s.get('name', 'N/A')}: {s.get('position', 'N/A')}")
        
        # Check certificates
        certs = data.get("certificates", [])
        print(f"Certificates: {len(certs)}")
        for c in certs[:3]:
            print(f"  - {c.get('title', 'N/A')}")
        
        # Check portfolio
        portfolio = data.get("portfolio_cases", [])
        print(f"Portfolio cases: {len(portfolio)}")
        for p in portfolio[:3]:
            print(f"  - {p.get('title', 'N/A')}")
    
    # ---- PUT /api/contractor/profile ----
    def test_update_profile_requires_auth(self):
        """PUT /api/contractor/profile requires authentication"""
        response = requests.put(f"{BASE_URL}/api/contractor/profile", json={"about": "test"})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_update_profile_saves_fields(self, auth_headers):
        """PUT /api/contractor/profile saves updated fields"""
        # First get current profile
        get_response = requests.get(f"{BASE_URL}/api/contractor/profile", headers=auth_headers)
        original_data = get_response.json()
        original_slogan = original_data.get("slogan", "")
        
        # Update with test data
        test_slogan = "TEST_SLOGAN_" + str(os.urandom(4).hex())
        update_data = {
            "slogan": test_slogan,
            "about": original_data.get("about", ""),
            "city": original_data.get("city", ""),
            "address": original_data.get("address", ""),
            "staff": original_data.get("staff", []),
            "certificates": original_data.get("certificates", []),
            "portfolio_cases": original_data.get("portfolio_cases", []),
            "working_hours": original_data.get("working_hours", ""),
            "languages": original_data.get("languages", []),
            "social_links": original_data.get("social_links", {})
        }
        
        response = requests.put(f"{BASE_URL}/api/contractor/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify update persisted
        verify_response = requests.get(f"{BASE_URL}/api/contractor/profile", headers=auth_headers)
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("slogan") == test_slogan, f"Slogan not updated: {verify_data.get('slogan')}"
        
        # Restore original slogan
        update_data["slogan"] = original_slogan
        requests.put(f"{BASE_URL}/api/contractor/profile", json=update_data, headers=auth_headers)
        print(f"Profile update test passed - slogan was updated and restored")
    
    # ---- POST /api/contractor/profile/files ----
    def test_upload_file_requires_auth(self):
        """POST /api/contractor/profile/files requires authentication"""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        data = {"category": "facility", "title": "Test"}
        response = requests.post(f"{BASE_URL}/api/contractor/profile/files", files=files, data=data)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_upload_file_works(self, auth_headers):
        """POST /api/contractor/profile/files uploads file successfully"""
        # Create a small test image (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {"file": ("test_image.png", png_data, "image/png")}
        data = {"category": "facility", "title": "TEST_UPLOAD_IMAGE"}
        
        response = requests.post(
            f"{BASE_URL}/api/contractor/profile/files",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert "id" in result, "Missing file id in response"
        assert result.get("category") == "facility", f"Wrong category: {result.get('category')}"
        
        print(f"File uploaded successfully: {result}")
        
        # Store file_id for cleanup
        return result["id"]
    
    # ---- DELETE /api/contractor/profile/files/{file_id} ----
    def test_delete_file_requires_auth(self):
        """DELETE /api/contractor/profile/files/{file_id} requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/contractor/profile/files/fake-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_delete_file_works(self, auth_headers):
        """DELETE /api/contractor/profile/files/{file_id} deletes file"""
        # First upload a file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {"file": ("test_delete.png", png_data, "image/png")}
        data = {"category": "certificate", "title": "TEST_DELETE_FILE"}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/contractor/profile/files",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["id"]
        
        # Delete the file
        delete_response = requests.delete(
            f"{BASE_URL}/api/contractor/profile/files/{file_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        print(f"File deleted successfully: {file_id}")
    
    def test_delete_nonexistent_file_returns_404(self, auth_headers):
        """DELETE /api/contractor/profile/files/{file_id} returns 404 for non-existent file"""
        response = requests.delete(
            f"{BASE_URL}/api/contractor/profile/files/nonexistent-file-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # ---- GET /api/profile-files/{file_id}/download ----
    def test_download_file_public(self, auth_headers):
        """GET /api/profile-files/{file_id}/download serves file without auth"""
        # First upload a file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {"file": ("test_download.png", png_data, "image/png")}
        data = {"category": "facility", "title": "TEST_DOWNLOAD_FILE"}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/contractor/profile/files",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["id"]
        
        # Download without auth (public endpoint)
        download_response = requests.get(f"{BASE_URL}/api/profile-files/{file_id}/download")
        assert download_response.status_code == 200, f"Expected 200, got {download_response.status_code}"
        assert len(download_response.content) > 0, "Downloaded file is empty"
        
        print(f"File downloaded successfully (public): {len(download_response.content)} bytes")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/contractor/profile/files/{file_id}", headers=auth_headers)
    
    def test_download_nonexistent_file_returns_404(self):
        """GET /api/profile-files/{file_id}/download returns 404 for non-existent file"""
        response = requests.get(f"{BASE_URL}/api/profile-files/nonexistent-file-id/download")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # ---- GET /api/contractors/{contractor_id}/page ----
    def test_public_page_no_auth_required(self):
        """GET /api/contractors/{contractor_id}/page works without auth"""
        response = requests.get(f"{BASE_URL}/api/contractors/{CONTRACTOR_ID}/page")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_public_page_returns_full_data(self):
        """GET /api/contractors/{contractor_id}/page returns contractor, profile, and files"""
        response = requests.get(f"{BASE_URL}/api/contractors/{CONTRACTOR_ID}/page")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "contractor" in data, "Missing contractor object"
        assert "profile" in data, "Missing profile object"
        assert "files" in data, "Missing files array"
        
        # Check contractor fields
        contractor = data["contractor"]
        assert "id" in contractor, "Missing contractor.id"
        assert "company_name" in contractor, "Missing contractor.company_name"
        assert "services" in contractor, "Missing contractor.services"
        assert "rating" in contractor, "Missing contractor.rating"
        assert "verified" in contractor, "Missing contractor.verified"
        
        print(f"Public page - Company: {contractor.get('company_name')}")
        print(f"Public page - Services: {contractor.get('services')}")
        print(f"Public page - Rating: {contractor.get('rating')}")
        print(f"Public page - Verified: {contractor.get('verified')}")
        
        # Check profile fields
        profile = data["profile"]
        print(f"Public page - Profile keys: {list(profile.keys()) if profile else 'empty'}")
        if profile:
            print(f"Public page - Slogan: {profile.get('slogan', 'N/A')}")
            print(f"Public page - About: {profile.get('about', 'N/A')[:100]}...")
            print(f"Public page - Staff: {len(profile.get('staff', []))} members")
            print(f"Public page - Certificates: {len(profile.get('certificates', []))}")
            print(f"Public page - Portfolio: {len(profile.get('portfolio_cases', []))}")
        
        # Check files
        files = data["files"]
        print(f"Public page - Files: {len(files)}")
        for f in files[:3]:
            print(f"  - {f.get('category')}: {f.get('original_name')}")
    
    def test_public_page_ola_cars_data(self):
        """GET /api/contractors/{contractor_id}/page returns OLa CARS data correctly"""
        response = requests.get(f"{BASE_URL}/api/contractors/{CONTRACTOR_ID}/page")
        assert response.status_code == 200
        data = response.json()
        
        contractor = data["contractor"]
        profile = data["profile"]
        
        # OLa CARS should have company name
        assert contractor.get("company_name"), "OLa CARS should have company_name"
        print(f"OLa CARS company name: {contractor.get('company_name')}")
        
        # Check if profile has pre-filled data
        if profile:
            has_about = bool(profile.get("about"))
            has_slogan = bool(profile.get("slogan"))
            has_staff = len(profile.get("staff", [])) > 0
            has_certs = len(profile.get("certificates", [])) > 0
            has_portfolio = len(profile.get("portfolio_cases", [])) > 0
            
            print(f"OLa CARS profile - has about: {has_about}")
            print(f"OLa CARS profile - has slogan: {has_slogan}")
            print(f"OLa CARS profile - has staff: {has_staff}")
            print(f"OLa CARS profile - has certificates: {has_certs}")
            print(f"OLa CARS profile - has portfolio: {has_portfolio}")
    
    def test_public_page_nonexistent_contractor_returns_404(self):
        """GET /api/contractors/{contractor_id}/page returns 404 for non-existent contractor"""
        response = requests.get(f"{BASE_URL}/api/contractors/nonexistent-contractor-id/page")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
