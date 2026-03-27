"""
Test suite for Contractor Application File Upload Feature
Tests:
- POST /api/contractor-applications/{app_id}/files - Upload file with category and title
- GET /api/contractor-applications/{app_id}/files - Get files list
- GET /api/application-files/{file_id}/download - Download file
- GET /api/moderator/applications - Returns applications WITH 'files' array
- POST /api/contractors/register - Returns application_id in response
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"

# Existing test application ID with 1 file
EXISTING_APP_ID = "7dfe0df3-2661-4e38-ba53-cab8a99851f4"


class TestContractorApplicationFiles:
    """Tests for contractor application file upload feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin/moderator token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping authenticated tests")
    
    # ==================== GET FILES LIST ====================
    
    def test_get_application_files_returns_list(self):
        """GET /api/contractor-applications/{app_id}/files returns files list"""
        response = requests.get(f"{BASE_URL}/api/contractor-applications/{EXISTING_APP_ID}/files")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 1, "Should have at least 1 file (test file)"
        
        # Verify file structure
        file = data[0]
        assert "id" in file, "File should have id"
        assert "application_id" in file, "File should have application_id"
        assert "category" in file, "File should have category"
        assert "title" in file, "File should have title"
        assert "original_name" in file, "File should have original_name"
        assert "saved_name" in file, "File should have saved_name"
        assert "size" in file, "File should have size"
        assert "mime_type" in file, "File should have mime_type"
        assert "created_at" in file, "File should have created_at"
        
        print(f"✓ GET files list returned {len(data)} file(s)")
    
    def test_get_application_files_nonexistent_app(self):
        """GET /api/contractor-applications/{app_id}/files returns empty for non-existent app"""
        response = requests.get(f"{BASE_URL}/api/contractor-applications/nonexistent-app-id/files")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 0, "Should return empty list for non-existent app"
        
        print("✓ GET files for non-existent app returns empty list")
    
    # ==================== UPLOAD FILE ====================
    
    def test_upload_file_to_application(self):
        """POST /api/contractor-applications/{app_id}/files uploads file with category and title"""
        # Create a test file
        test_content = b"Test file content for upload test"
        files = {
            'file': ('test_upload.txt', io.BytesIO(test_content), 'text/plain')
        }
        data = {
            'category': 'license',
            'title': 'Test License Document'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor-applications/{EXISTING_APP_ID}/files",
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert "id" in result, "Response should have file id"
        assert result["category"] == "license", f"Category should be 'license', got {result.get('category')}"
        assert result["original_name"] == "test_upload.txt", f"Original name mismatch"
        
        # Store file_id for download test
        self.__class__.uploaded_file_id = result["id"]
        
        print(f"✓ File uploaded successfully with id: {result['id']}")
    
    def test_upload_file_nonexistent_app(self):
        """POST /api/contractor-applications/{app_id}/files returns 404 for non-existent app"""
        test_content = b"Test content"
        files = {
            'file': ('test.txt', io.BytesIO(test_content), 'text/plain')
        }
        data = {
            'category': 'document',
            'title': 'Test'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor-applications/nonexistent-app-id/files",
            files=files,
            data=data
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Upload to non-existent app returns 404")
    
    def test_upload_file_with_different_categories(self):
        """POST /api/contractor-applications/{app_id}/files supports all category types"""
        categories = ['document', 'certificate', 'license', 'photo', 'portfolio']
        
        for category in categories:
            test_content = f"Test content for {category}".encode()
            files = {
                'file': (f'test_{category}.txt', io.BytesIO(test_content), 'text/plain')
            }
            data = {
                'category': category,
                'title': f'Test {category.capitalize()}'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/contractor-applications/{EXISTING_APP_ID}/files",
                files=files,
                data=data
            )
            
            assert response.status_code == 200, f"Failed for category '{category}': {response.text}"
            result = response.json()
            assert result["category"] == category, f"Category mismatch for {category}"
        
        print(f"✓ All {len(categories)} categories supported")
    
    # ==================== DOWNLOAD FILE ====================
    
    def test_download_file(self):
        """GET /api/application-files/{file_id}/download serves the file"""
        # First get the list of files to get a valid file_id
        list_response = requests.get(f"{BASE_URL}/api/contractor-applications/{EXISTING_APP_ID}/files")
        assert list_response.status_code == 200
        files = list_response.json()
        assert len(files) > 0, "Need at least one file to test download"
        
        file_id = files[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/application-files/{file_id}/download")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert len(response.content) > 0, "Downloaded file should have content"
        
        # Check content-disposition header for filename
        content_disp = response.headers.get('content-disposition', '')
        assert 'filename' in content_disp.lower() or response.status_code == 200, "Should have filename in header or return content"
        
        print(f"✓ File downloaded successfully, size: {len(response.content)} bytes")
    
    def test_download_nonexistent_file(self):
        """GET /api/application-files/{file_id}/download returns 404 for non-existent file"""
        response = requests.get(f"{BASE_URL}/api/application-files/nonexistent-file-id/download")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Download non-existent file returns 404")
    
    # ==================== MODERATOR APPLICATIONS WITH FILES ====================
    
    def test_moderator_applications_includes_files(self, admin_token):
        """GET /api/moderator/applications returns applications WITH 'files' array"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/moderator/applications", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find our test application
        test_app = None
        for app in data:
            if app.get("id") == EXISTING_APP_ID:
                test_app = app
                break
        
        assert test_app is not None, f"Test application {EXISTING_APP_ID} not found in moderator applications"
        assert "files" in test_app, "Application should have 'files' field"
        assert isinstance(test_app["files"], list), "'files' should be a list"
        assert len(test_app["files"]) >= 1, "Test application should have at least 1 file"
        
        # Verify file structure in moderator response
        file = test_app["files"][0]
        assert "id" in file, "File should have id"
        assert "category" in file, "File should have category"
        assert "title" in file, "File should have title"
        
        print(f"✓ Moderator applications includes files array with {len(test_app['files'])} file(s)")
    
    def test_moderator_applications_requires_auth(self):
        """GET /api/moderator/applications requires authentication"""
        response = requests.get(f"{BASE_URL}/api/moderator/applications")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Moderator applications requires authentication")
    
    # ==================== CONTRACTOR REGISTER RETURNS APPLICATION_ID ====================
    
    def test_contractor_register_returns_application_id(self):
        """POST /api/contractors/register returns application_id in response"""
        import uuid
        unique_email = f"test_contractor_{uuid.uuid4().hex[:8]}@test.com"
        
        register_data = {
            "company_name": "Test Company",
            "country": "BY",
            "registration_number": "123456789",
            "legal_address": "Test Address",
            "contact_person": "Test Person",
            "position": "Director",
            "phone": "+375291234567",
            "email": unique_email,
            "password": "testpass123",
            "whatsapp": "",
            "wechat": "",
            "telegram": "",
            "website": "",
            "services": ["inspection", "export"],
            "service_prices": {"inspection": 100, "export": 200},
            "description": "Test company description",
            "experience_years": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=register_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "application_id" in data, "Response should contain 'application_id'"
        assert data["application_id"] is not None, "application_id should not be None"
        assert len(data["application_id"]) > 0, "application_id should not be empty"
        
        # Also check contractor_id is present
        assert "contractor_id" in data, "Response should contain 'contractor_id'"
        
        print(f"✓ Contractor register returns application_id: {data['application_id']}")
        
        # Store for cleanup or further tests
        self.__class__.registered_app_id = data["application_id"]
    
    def test_contractor_register_duplicate_email(self):
        """POST /api/contractors/register rejects duplicate email"""
        # Try to register with same email as existing application
        register_data = {
            "company_name": "Duplicate Company",
            "country": "BY",
            "registration_number": "987654321",
            "legal_address": "Test Address",
            "contact_person": "Test Person",
            "position": "Director",
            "phone": "+375291234567",
            "email": "votin@tut.by",  # Existing email
            "password": "testpass123",
            "services": ["inspection"],
            "service_prices": {"inspection": 100},
            "description": "Test"
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=register_data)
        
        # Should fail with 400 for duplicate email
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        print("✓ Contractor register rejects duplicate email")


class TestFileUploadAfterRegistration:
    """Test uploading files immediately after contractor registration"""
    
    def test_register_and_upload_files(self):
        """Full flow: Register contractor, get application_id, upload files"""
        import uuid
        unique_email = f"test_flow_{uuid.uuid4().hex[:8]}@test.com"
        
        # Step 1: Register contractor
        register_data = {
            "company_name": "Flow Test Company",
            "country": "CN",
            "registration_number": "91310000MA1FL5XX0L",
            "legal_address": "Shanghai, China",
            "contact_person": "Li Wei",
            "position": "Manager",
            "phone": "+8613812345678",
            "email": unique_email,
            "password": "testpass123",
            "services": ["inspection", "logistics_china"],
            "service_prices": {"inspection": 150, "logistics_china": 500},
            "description": "Full flow test company"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/contractors/register", json=register_data)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        app_id = reg_response.json().get("application_id")
        assert app_id, "No application_id returned"
        
        print(f"✓ Step 1: Registered contractor with application_id: {app_id}")
        
        # Step 2: Upload certificate file
        cert_content = b"Certificate content for flow test"
        files = {
            'file': ('certificate.pdf', io.BytesIO(cert_content), 'application/pdf')
        }
        data = {
            'category': 'certificate',
            'title': 'Business License'
        }
        
        upload_response = requests.post(
            f"{BASE_URL}/api/contractor-applications/{app_id}/files",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200, f"Certificate upload failed: {upload_response.text}"
        cert_file_id = upload_response.json().get("id")
        
        print(f"✓ Step 2: Uploaded certificate with file_id: {cert_file_id}")
        
        # Step 3: Upload photo file
        photo_content = b"Photo content for flow test"
        files = {
            'file': ('facility.jpg', io.BytesIO(photo_content), 'image/jpeg')
        }
        data = {
            'category': 'photo',
            'title': 'Facility Photo'
        }
        
        upload_response = requests.post(
            f"{BASE_URL}/api/contractor-applications/{app_id}/files",
            files=files,
            data=data
        )
        assert upload_response.status_code == 200, f"Photo upload failed: {upload_response.text}"
        
        print("✓ Step 3: Uploaded facility photo")
        
        # Step 4: Verify files are listed
        list_response = requests.get(f"{BASE_URL}/api/contractor-applications/{app_id}/files")
        assert list_response.status_code == 200
        files_list = list_response.json()
        assert len(files_list) == 2, f"Expected 2 files, got {len(files_list)}"
        
        print(f"✓ Step 4: Verified {len(files_list)} files in application")
        
        # Step 5: Download certificate file
        download_response = requests.get(f"{BASE_URL}/api/application-files/{cert_file_id}/download")
        assert download_response.status_code == 200, f"Download failed: {download_response.text}"
        
        print("✓ Step 5: Downloaded certificate file successfully")
        
        print("\n✓ Full registration + file upload flow completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
