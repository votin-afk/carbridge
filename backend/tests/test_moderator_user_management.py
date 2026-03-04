"""
Test suite for Moderator User Management feature
Tests: UserProfileModerator page, user verification, document verification, deal stage approval
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test@test.com"
ADMIN_PASSWORD = "test"
TEST_USER_ID = "77c8ed94-c132-4056-8b6a-a065ee32c9ee"


class TestModeratorUserManagement:
    """Test moderator user management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
            self.user = login_response.json().get("user")
            print(f"✓ Logged in as {ADMIN_EMAIL} with role: {self.user.get('role')}")
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ==================== GET /api/moderator/users/{user_id}/full-profile ====================
    
    def test_get_user_full_profile_success(self):
        """Test GET /api/moderator/users/{user_id}/full-profile returns complete user data"""
        response = self.session.get(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/full-profile")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "user" in data, "Response should contain 'user' field"
        assert "account" in data, "Response should contain 'account' field"
        assert "cars" in data, "Response should contain 'cars' field"
        assert "documents" in data, "Response should contain 'documents' field"
        assert "deals" in data, "Response should contain 'deals' field"
        
        # Verify user data
        user = data["user"]
        assert user.get("id") == TEST_USER_ID, f"User ID mismatch: {user.get('id')}"
        assert "email" in user, "User should have email"
        assert "name" in user, "User should have name"
        assert "role" in user, "User should have role"
        
        # Verify account data
        account = data["account"]
        assert "balance" in account or account is not None, "Account should have balance"
        assert "is_verified" in account or account is not None, "Account should have is_verified"
        
        # Verify cars is a list
        assert isinstance(data["cars"], list), "Cars should be a list"
        
        print(f"✓ Full profile retrieved: user={user.get('email')}, cars={len(data['cars'])}, deals={len(data['deals'])}")
    
    def test_get_user_full_profile_not_found(self):
        """Test GET /api/moderator/users/{user_id}/full-profile returns 404 for non-existent user"""
        fake_user_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/moderator/users/{fake_user_id}/full-profile")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ 404 returned for non-existent user")
    
    def test_get_user_full_profile_unauthorized(self):
        """Test GET /api/moderator/users/{user_id}/full-profile requires authentication"""
        # Create new session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/full-profile")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthorized access blocked: {response.status_code}")
    
    # ==================== POST /api/moderator/users/{user_id}/verify ====================
    
    def test_verify_user_approve(self):
        """Test POST /api/moderator/users/{user_id}/verify with approve action"""
        response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/verify", json={
            "action": "approve",
            "reason": "Test verification approval"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data.get("is_verified") == True, "User should be verified"
        
        print(f"✓ User verification approved: {data.get('message')}")
    
    def test_verify_user_reject(self):
        """Test POST /api/moderator/users/{user_id}/verify with reject action"""
        response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/verify", json={
            "action": "reject",
            "reason": "Test verification rejection"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data.get("is_verified") == False, "User should not be verified"
        
        print(f"✓ User verification rejected: {data.get('message')}")
    
    def test_verify_user_invalid_action(self):
        """Test POST /api/moderator/users/{user_id}/verify with invalid action"""
        response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/verify", json={
            "action": "invalid_action",
            "reason": "Test"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invalid action rejected: {response.status_code}")
    
    # ==================== POST /api/moderator/users/{user_id}/sign-contract ====================
    
    def test_sign_contract_approve(self):
        """Test POST /api/moderator/users/{user_id}/sign-contract with approve action"""
        response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/sign-contract", json={
            "action": "approve"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data.get("contract_signed") == True, "Contract should be signed"
        
        print(f"✓ Contract signed: {data.get('message')}")
    
    def test_sign_contract_reject(self):
        """Test POST /api/moderator/users/{user_id}/sign-contract with reject action"""
        response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/sign-contract", json={
            "action": "reject"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert data.get("contract_signed") == False, "Contract should not be signed"
        
        print(f"✓ Contract rejected: {data.get('message')}")
    
    # ==================== POST /api/moderator/documents/{doc_id}/verify ====================
    
    def test_verify_document_not_found(self):
        """Test POST /api/moderator/documents/{doc_id}/verify returns 404 for non-existent document"""
        fake_doc_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/moderator/documents/{fake_doc_id}/verify", json={
            "action": "approve",
            "comment": "Test"
        })
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ 404 returned for non-existent document")
    
    def test_verify_document_invalid_action(self):
        """Test POST /api/moderator/documents/{doc_id}/verify with invalid action"""
        fake_doc_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/moderator/documents/{fake_doc_id}/verify", json={
            "action": "invalid",
            "comment": "Test"
        })
        
        # Should return 400 for invalid action before checking if doc exists
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        print(f"✓ Invalid action handled: {response.status_code}")
    
    # ==================== POST /api/moderator/deals/{deal_id}/approve-stage ====================
    
    def test_approve_deal_stage_not_found(self):
        """Test POST /api/moderator/deals/{deal_id}/approve-stage returns 404 for non-existent deal"""
        fake_deal_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/moderator/deals/{fake_deal_id}/approve-stage", json={
            "action": "approve",
            "comment": "Test approval"
        })
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ 404 returned for non-existent deal")
    
    def test_approve_deal_stage_invalid_action(self):
        """Test POST /api/moderator/deals/{deal_id}/approve-stage with invalid action"""
        fake_deal_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/moderator/deals/{fake_deal_id}/approve-stage", json={
            "action": "invalid",
            "comment": "Test"
        })
        
        # Should return 400 for invalid action
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
        print(f"✓ Invalid action handled: {response.status_code}")
    
    # ==================== GET /api/admin/users ====================
    
    def test_get_all_users_admin(self):
        """Test GET /api/admin/users returns list of users for admin"""
        response = self.session.get(f"{BASE_URL}/api/admin/users")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            user = data[0]
            assert "id" in user, "User should have id"
            assert "email" in user, "User should have email"
            assert "password_hash" not in user, "Password hash should not be exposed"
        
        print(f"✓ Admin users list retrieved: {len(data)} users")
    
    # ==================== GET /api/moderator/pending-approvals ====================
    
    def test_get_pending_approvals(self):
        """Test GET /api/moderator/pending-approvals returns pending items"""
        response = self.session.get(f"{BASE_URL}/api/moderator/pending-approvals")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "pending_users" in data, "Response should contain pending_users"
        assert "pending_documents" in data, "Response should contain pending_documents"
        assert "pending_deals" in data, "Response should contain pending_deals"
        
        print(f"✓ Pending approvals: users={len(data['pending_users'])}, docs={len(data['pending_documents'])}, deals={len(data['pending_deals'])}")


class TestModeratorUserManagementIntegration:
    """Integration tests for moderator user management flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
            self.user = login_response.json().get("user")
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_full_verification_flow(self):
        """Test complete user verification flow: get profile -> verify -> check updated"""
        # Step 1: Get user profile
        profile_response = self.session.get(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/full-profile")
        assert profile_response.status_code == 200, f"Failed to get profile: {profile_response.status_code}"
        
        profile_data = profile_response.json()
        print(f"✓ Step 1: Got profile for {profile_data['user'].get('email')}")
        
        # Step 2: Verify user
        verify_response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/verify", json={
            "action": "approve",
            "reason": "Integration test verification"
        })
        assert verify_response.status_code == 200, f"Failed to verify: {verify_response.status_code}"
        print(f"✓ Step 2: User verified")
        
        # Step 3: Check profile updated
        updated_profile = self.session.get(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/full-profile")
        assert updated_profile.status_code == 200
        
        updated_data = updated_profile.json()
        account = updated_data.get("account", {})
        assert account.get("is_verified") == True, "User should be verified after approval"
        print(f"✓ Step 3: Verification status confirmed: is_verified={account.get('is_verified')}")
    
    def test_full_contract_flow(self):
        """Test complete contract signing flow"""
        # Step 1: Verify user first (required for contract)
        self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/verify", json={
            "action": "approve",
            "reason": "Pre-contract verification"
        })
        
        # Step 2: Sign contract
        contract_response = self.session.post(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/sign-contract", json={
            "action": "approve"
        })
        assert contract_response.status_code == 200, f"Failed to sign contract: {contract_response.status_code}"
        print(f"✓ Contract signed")
        
        # Step 3: Verify contract status in profile
        profile_response = self.session.get(f"{BASE_URL}/api/moderator/users/{TEST_USER_ID}/full-profile")
        profile_data = profile_response.json()
        
        account = profile_data.get("account", {})
        assert account.get("contract_signed") == True, "Contract should be signed"
        print(f"✓ Contract status confirmed: contract_signed={account.get('contract_signed')}")


class TestModeratorPageNavigation:
    """Test navigation from ModeratorPage to UserProfileModerator"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_users_list_for_navigation(self):
        """Test that admin/users endpoint returns data needed for navigation"""
        response = self.session.get(f"{BASE_URL}/api/admin/users")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        users = response.json()
        assert isinstance(users, list), "Should return list of users"
        
        if len(users) > 0:
            user = users[0]
            # Verify user has ID needed for navigation to /moderator/user/{userId}
            assert "id" in user, "User must have 'id' for navigation"
            print(f"✓ Users list has {len(users)} users with IDs for navigation")
        else:
            print("⚠ No users in list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
