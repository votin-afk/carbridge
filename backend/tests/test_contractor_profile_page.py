"""
Test suite for Contractor Public Profile Page feature
Tests:
- GET /api/contractors/{id}/page - public profile endpoint
- Contractor data structure validation
- Services localization
- Profile and files data
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com')

# Test contractor ID from the review request
TEST_CONTRACTOR_ID = "c1f8fc8e-b0c7-45a6-bdda-5eaf9c792a3e"


class TestContractorPublicProfilePage:
    """Tests for the public contractor profile page endpoint"""
    
    def test_get_contractor_page_success(self):
        """Test GET /api/contractors/{id}/page returns contractor data"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "contractor" in data, "Response should contain 'contractor' key"
        assert "profile" in data, "Response should contain 'profile' key"
        assert "files" in data, "Response should contain 'files' key"
        
        print(f"✓ GET /api/contractors/{TEST_CONTRACTOR_ID}/page returns correct structure")
    
    def test_contractor_data_fields(self):
        """Test contractor data contains required fields"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        data = response.json()
        
        contractor = data["contractor"]
        
        # Required fields
        required_fields = ["id", "company_name", "services", "rating", "completed_deals"]
        for field in required_fields:
            assert field in contractor, f"Contractor should have '{field}' field"
        
        # Verify company name
        assert contractor["company_name"] == "АвтоПодбор Шанхай", f"Expected 'АвтоПодбор Шанхай', got {contractor['company_name']}"
        
        # Verify services is present
        assert contractor["services"], "Services should not be empty"
        
        print(f"✓ Contractor data contains all required fields")
        print(f"  - Company: {contractor['company_name']}")
        print(f"  - Services: {contractor['services']}")
        print(f"  - Rating: {contractor['rating']}")
    
    def test_contractor_contact_info(self):
        """Test contractor has contact information"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        data = response.json()
        
        contractor = data["contractor"]
        
        # Contact fields
        contact_fields = ["phone", "email", "contact_person"]
        has_contact = any(contractor.get(f) for f in contact_fields)
        
        assert has_contact, "Contractor should have at least one contact method"
        
        print(f"✓ Contractor has contact information")
        print(f"  - Phone: {contractor.get('phone', 'N/A')}")
        print(f"  - Email: {contractor.get('email', 'N/A')}")
        print(f"  - Contact person: {contractor.get('contact_person', 'N/A')}")
    
    def test_profile_data_structure(self):
        """Test profile data has expected structure"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        data = response.json()
        
        profile = data["profile"]
        
        # Profile should have these fields (may be empty)
        expected_fields = ["contractor_id", "about", "staff", "certificates", "portfolio_cases"]
        for field in expected_fields:
            assert field in profile, f"Profile should have '{field}' field"
        
        print(f"✓ Profile data has correct structure")
        print(f"  - About: {profile.get('about', '')[:50]}...")
    
    def test_files_is_list(self):
        """Test files is a list"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        data = response.json()
        
        files = data["files"]
        
        assert isinstance(files, list), "Files should be a list"
        
        print(f"✓ Files is a list with {len(files)} items")
    
    def test_nonexistent_contractor_returns_404(self):
        """Test requesting non-existent contractor returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/contractors/{fake_id}/page")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print(f"✓ Non-existent contractor returns 404")
    
    def test_no_auth_required(self):
        """Test endpoint is public (no auth required)"""
        # Make request without any auth headers
        response = requests.get(
            f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page",
            headers={}  # No auth
        )
        
        assert response.status_code == 200, f"Expected 200 without auth, got {response.status_code}"
        
        print(f"✓ Endpoint is public (no auth required)")


class TestContractorsListEndpoint:
    """Tests for the contractors list endpoint"""
    
    def test_get_contractors_list(self):
        """Test GET /api/contractors returns list"""
        response = requests.get(f"{BASE_URL}/api/contractors")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/contractors returns list with {len(data)} contractors")
    
    def test_contractors_by_type(self):
        """Test filtering contractors by type"""
        response = requests.get(f"{BASE_URL}/api/contractors?contractor_type=inspection")
        
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Contractors filtered by type 'inspection': {len(data)} found")
    
    def test_contractor_has_services(self):
        """Test contractor in list has services field"""
        response = requests.get(f"{BASE_URL}/api/contractors?contractor_type=inspection")
        data = response.json()
        
        if data:
            contractor = data[0]
            assert "services" in contractor, "Contractor should have 'services' field"
            print(f"✓ Contractor services: {contractor.get('services')}")


class TestContractorApprovalFlow:
    """Tests for contractor approval flow (requires moderator auth)"""
    
    @pytest.fixture
    def moderator_token(self):
        """Get moderator auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "votin@tut.by", "password": "test"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not authenticate as moderator")
    
    def test_approved_contractor_in_list(self):
        """Test approved contractor appears in public list"""
        response = requests.get(f"{BASE_URL}/api/contractors?contractor_type=inspection")
        data = response.json()
        
        # Check if our test contractor is in the list
        contractor_ids = [c["id"] for c in data]
        
        assert TEST_CONTRACTOR_ID in contractor_ids, f"Approved contractor {TEST_CONTRACTOR_ID} should be in list"
        
        print(f"✓ Approved contractor appears in public list")
    
    def test_contractor_verified_status(self):
        """Test contractor has verified status"""
        response = requests.get(f"{BASE_URL}/api/contractors/{TEST_CONTRACTOR_ID}/page")
        data = response.json()
        
        contractor = data["contractor"]
        
        # Check verified status
        is_verified = contractor.get("verified") or contractor.get("is_verified")
        
        assert is_verified, "Approved contractor should be verified"
        
        print(f"✓ Contractor is verified: {is_verified}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
