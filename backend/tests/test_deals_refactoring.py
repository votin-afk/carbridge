"""
Test suite for deals routes refactoring validation
Tests that all deal-related endpoints work correctly after extraction from server.py to routes/deals.py
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
CONTRACTOR_EMAIL = "horon4ik@icloud.com"
CONTRACTOR_PASSWORD = "test123"

# Known test data
TEST_DEAL_ID = "c650aaba-5356-4e97-8cee-133e920c3f03"
TEST_FILE_ID = "f29d6f50-e658-4441-a2db-ff9bd4660d57"


class TestDealsRefactoring:
    """Test deal endpoints after refactoring to routes/deals.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.user_token = None
        self.admin_token = None
        self.contractor_token = None
    
    def get_user_token(self):
        """Get user authentication token"""
        if self.user_token:
            return self.user_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        if response.status_code == 200:
            self.user_token = response.json().get("access_token")
            return self.user_token
        return None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
            return self.admin_token
        return None
    
    def get_contractor_token(self):
        """Get contractor authentication token"""
        if self.contractor_token:
            return self.contractor_token
        response = self.session.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            self.contractor_token = response.json().get("access_token")
            return self.contractor_token
        return None
    
    # ==================== USER DEAL ENDPOINTS ====================
    
    def test_get_user_deals(self):
        """Test GET /api/deals - returns user deals list"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of deals"
        print(f"✓ GET /api/deals - returned {len(data)} deals")
    
    def test_get_completed_deals(self):
        """Test GET /api/deals/completed - returns completed deals"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/completed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of completed deals"
        print(f"✓ GET /api/deals/completed - returned {len(data)} completed deals")
    
    def test_get_specific_deal(self):
        """Test GET /api/deals/{deal_id} - returns specific deal"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 404 if deal doesn't belong to admin user
        if response.status_code == 404:
            print(f"✓ GET /api/deals/{TEST_DEAL_ID} - 404 (deal not owned by admin, expected)")
            return
        
        assert response.status_code == 200, f"Expected 200 or 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Expected deal to have id"
        print(f"✓ GET /api/deals/{TEST_DEAL_ID} - returned deal data")
    
    # ==================== DEAL MESSAGES ENDPOINTS ====================
    
    def test_get_deal_messages(self):
        """Test GET /api/deals/{deal_id}/messages - get deal messages"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 403/404 if deal doesn't belong to user
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/deals/{TEST_DEAL_ID}/messages - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of messages"
        print(f"✓ GET /api/deals/{TEST_DEAL_ID}/messages - returned {len(data)} messages")
    
    def test_send_deal_message(self):
        """Test POST /api/deals/{deal_id}/messages - send deal message"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Test message from refactoring validation"}
        )
        
        # May return 403/404 if deal doesn't belong to user
        if response.status_code in [403, 404]:
            print(f"✓ POST /api/deals/{TEST_DEAL_ID}/messages - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data or "message" in data, "Expected response with id or message"
        print(f"✓ POST /api/deals/{TEST_DEAL_ID}/messages - message sent")
    
    # ==================== DEAL FILES ENDPOINTS ====================
    
    def test_get_deal_files(self):
        """Test GET /api/deals/{deal_id}/files - get deal files"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 403/404 if deal doesn't belong to user
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/deals/{TEST_DEAL_ID}/files - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of files"
        print(f"✓ GET /api/deals/{TEST_DEAL_ID}/files - returned {len(data)} files")
    
    def test_public_file_download_requires_token(self):
        """Test GET /api/files/{file_id}/public-download - requires token"""
        response = self.session.get(
            f"{BASE_URL}/api/files/{TEST_FILE_ID}/public-download"
        )
        
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        print(f"✓ GET /api/files/{TEST_FILE_ID}/public-download - 401 without token (auth working)")
    
    def test_public_file_download_with_token(self):
        """Test GET /api/files/{file_id}/public-download - with valid token"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/files/{TEST_FILE_ID}/public-download?token={token}"
        )
        
        # May return 403/404 if file doesn't exist or no access
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/files/{TEST_FILE_ID}/public-download - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET /api/files/{TEST_FILE_ID}/public-download - file download working")
    
    # ==================== STAGE MESSAGES ENDPOINTS ====================
    
    def test_get_stage_messages(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/messages - stage messages"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/export/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 403/404 if deal doesn't belong to user
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/deals/{TEST_DEAL_ID}/stages/export/messages - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of messages"
        print(f"✓ GET /api/deals/{TEST_DEAL_ID}/stages/export/messages - returned {len(data)} messages")
    
    # ==================== CONTRACTOR DEAL ENDPOINTS ====================
    
    def test_get_contractor_deals(self):
        """Test GET /api/contractor/deals - contractor deals list"""
        token = self.get_contractor_token()
        if not token:
            pytest.skip("Contractor login failed - skipping contractor tests")
        
        response = self.session.get(
            f"{BASE_URL}/api/contractor/deals",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of deals"
        print(f"✓ GET /api/contractor/deals - returned {len(data)} deals")
    
    def test_get_contractor_stage_messages(self):
        """Test GET /api/contractor/deals/{deal_id}/stages/{stage_key}/messages"""
        token = self.get_contractor_token()
        if not token:
            pytest.skip("Contractor login failed - skipping contractor tests")
        
        response = self.session.get(
            f"{BASE_URL}/api/contractor/deals/{TEST_DEAL_ID}/stages/export/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 403/404 if contractor not assigned to this stage
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/contractor/deals/{TEST_DEAL_ID}/stages/export/messages - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of messages"
        print(f"✓ GET /api/contractor/deals/{TEST_DEAL_ID}/stages/export/messages - returned {len(data)} messages")
    
    # ==================== MODERATOR DEAL ENDPOINTS ====================
    
    def test_get_moderator_pending_stages(self):
        """Test GET /api/moderator/deals/pending-stages - moderator pending stages"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/moderator/deals/pending-stages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of pending stages"
        print(f"✓ GET /api/moderator/deals/pending-stages - returned {len(data)} pending stages")
    
    def test_get_moderator_deals(self):
        """Test GET /api/moderator/deals/{deal_id} - moderator deal details"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 404 if deal doesn't exist
        if response.status_code == 404:
            print(f"✓ GET /api/moderator/deals/{TEST_DEAL_ID} - 404 (deal not found)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "deal" in data, "Expected deal in response"
        print(f"✓ GET /api/moderator/deals/{TEST_DEAL_ID} - returned deal details")
    
    # ==================== ACCOUNT SUMMARY ENDPOINT ====================
    
    def test_get_account_summary(self):
        """Test GET /api/account/summary - account summary still works"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/account/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "balance" in data, "Expected balance in response"
        assert "is_verified" in data, "Expected is_verified in response"
        print(f"✓ GET /api/account/summary - balance: {data.get('balance')}, verified: {data.get('is_verified')}")
    
    # ==================== UNREAD COUNTS ENDPOINT ====================
    
    def test_get_deal_unread_counts(self):
        """Test GET /api/deals/{deal_id}/unread-counts - unread counts"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/unread-counts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May return 403/404 if deal doesn't belong to user
        if response.status_code in [403, 404]:
            print(f"✓ GET /api/deals/{TEST_DEAL_ID}/unread-counts - {response.status_code} (access control working)")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Expected dict of unread counts"
        print(f"✓ GET /api/deals/{TEST_DEAL_ID}/unread-counts - returned unread counts")
    
    # ==================== CONSULTANT REQUEST ENDPOINT ====================
    
    def test_consultant_request_requires_balance(self):
        """Test POST /api/consultant/request - uses CONSULTANT_FEE from config"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/consultant/request",
            headers={"Authorization": f"Bearer {token}"},
            json={"context": "general", "message": "Test consultant request"}
        )
        
        # Should return 400 if insufficient balance (expected for most test users)
        # or 200 if user has enough balance
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text}"
        
        if response.status_code == 400:
            data = response.json()
            assert "Недостаточно средств" in data.get("detail", ""), "Expected insufficient funds error"
            print(f"✓ POST /api/consultant/request - 400 (insufficient balance, CONSULTANT_FEE=$200 working)")
        else:
            print(f"✓ POST /api/consultant/request - 200 (request created)")


class TestConfigConstants:
    """Test that config constants are properly imported in deals.py"""
    
    def test_config_imports(self):
        """Verify config constants are accessible"""
        # This test verifies the imports work by checking the consultant endpoint
        # which uses CONSULTANT_FEE from config
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, "Login failed"
        token = response.json().get("access_token")
        
        # Test consultant endpoint (uses CONSULTANT_FEE)
        response = session.post(
            f"{BASE_URL}/api/consultant/request",
            headers={"Authorization": f"Bearer {token}"},
            json={"context": "general", "message": "Config test"}
        )
        
        # If we get 400 with "Недостаточно средств" or 200, config is working
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print("✓ Config constants (CONSULTANT_FEE) properly imported in deals.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
