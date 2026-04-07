"""
Test suite for Help Requests feature
Tests: Create help request, get user requests, send messages, moderator management, manager assignment, chat
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = {"email": "votin@tut.by", "password": "test"}
STANDARD_USER = {"email": "test@test.com", "password": "test"}


class TestHelpRequestsAuth:
    """Test authentication for help request endpoints"""
    
    def test_help_requests_requires_auth(self):
        """GET /api/help-requests requires authentication"""
        response = requests.get(f"{BASE_URL}/api/help-requests")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ GET /api/help-requests requires auth ({response.status_code})")
    
    def test_moderator_help_requests_requires_auth(self):
        """GET /api/moderator/help-requests requires authentication"""
        response = requests.get(f"{BASE_URL}/api/moderator/help-requests")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ GET /api/moderator/help-requests requires auth ({response.status_code})")


class TestUserHelpRequests:
    """Test user-facing help request endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as standard user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STANDARD_USER)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.user_id = data.get("user", {}).get("id")
        else:
            pytest.skip(f"Login failed: {response.status_code}")
    
    def test_get_user_help_requests(self):
        """GET /api/help-requests returns user's help requests"""
        response = requests.get(f"{BASE_URL}/api/help-requests", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/help-requests returns {len(data)} requests")
        return data
    
    def test_create_help_request(self):
        """POST /api/help-requests creates a new help request"""
        test_description = f"TEST_help_request_{uuid.uuid4().hex[:8]}"
        payload = {
            "request_type": "general",
            "description": test_description
        }
        response = requests.post(f"{BASE_URL}/api/help-requests", json=payload, headers=self.headers)
        
        # May return 403 if prepayment not confirmed - that's expected behavior
        if response.status_code == 403:
            detail = response.json().get("detail", "")
            assert "предоплату" in detail.lower() or "prepayment" in detail.lower()
            print("✓ POST /api/help-requests returns 403 for user without prepayment (expected)")
            pytest.skip("User doesn't have prepayment confirmed")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "request_id" in data, "Response should contain request_id"
        assert "message" in data, "Response should contain message"
        print(f"✓ POST /api/help-requests created request: {data.get('request_id')}")
        return data.get("request_id")
    
    def test_get_specific_help_request(self):
        """GET /api/help-requests/{id} returns specific request with messages"""
        # First get list of requests
        list_response = requests.get(f"{BASE_URL}/api/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        if not requests_list:
            pytest.skip("No help requests found for user")
        
        request_id = requests_list[0]["id"]
        response = requests.get(f"{BASE_URL}/api/help-requests/{request_id}", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert "messages" in data, "Response should contain messages array"
        assert "status" in data, "Response should contain status"
        print(f"✓ GET /api/help-requests/{request_id} returns request with {len(data.get('messages', []))} messages")
        return data
    
    def test_send_message_to_help_request(self):
        """POST /api/help-requests/{id}/messages sends client message"""
        # Get a help request
        list_response = requests.get(f"{BASE_URL}/api/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        if not requests_list:
            pytest.skip("No help requests found for user")
        
        request_id = requests_list[0]["id"]
        test_message = f"TEST_message_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/help-requests/{request_id}/messages",
            json={"content": test_message},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"✓ POST /api/help-requests/{request_id}/messages sent message successfully")
        
        # Verify message was added
        verify_response = requests.get(f"{BASE_URL}/api/help-requests/{request_id}", headers=self.headers)
        if verify_response.status_code == 200:
            messages = verify_response.json().get("messages", [])
            found = any(m.get("content") == test_message for m in messages)
            assert found, "Message should be in the request's messages"
            print("✓ Message verified in request's messages array")


class TestModeratorHelpRequests:
    """Test moderator/admin help request management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.user = data.get("user", {})
        else:
            pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_get_all_help_requests(self):
        """GET /api/moderator/help-requests returns all help requests"""
        response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/moderator/help-requests returns {len(data)} requests")
        
        # Check structure if there are requests
        if data:
            req = data[0]
            assert "id" in req, "Request should have id"
            assert "status" in req, "Request should have status"
            assert "user_id" in req, "Request should have user_id"
            print(f"  First request: id={req['id'][:8]}..., status={req['status']}")
        return data
    
    def test_get_available_managers(self):
        """GET /api/moderator/available-managers returns list of moderators/admins"""
        response = requests.get(f"{BASE_URL}/api/moderator/available-managers", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/moderator/available-managers returns {len(data)} managers")
        
        # Check structure
        if data:
            manager = data[0]
            assert "id" in manager, "Manager should have id"
            assert "role" in manager, "Manager should have role"
            assert manager["role"] in ["moderator", "admin"], f"Manager role should be moderator/admin, got {manager['role']}"
            print(f"  First manager: {manager.get('name', '')} {manager.get('last_name', '')} ({manager['role']})")
        return data
    
    def test_get_specific_help_request_moderator(self):
        """GET /api/moderator/help-requests/{id} returns request with messages"""
        # First get list
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        if not requests_list:
            pytest.skip("No help requests found")
        
        request_id = requests_list[0]["id"]
        response = requests.get(f"{BASE_URL}/api/moderator/help-requests/{request_id}", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert "messages" in data, "Response should contain messages (including system messages)"
        assert "status" in data, "Response should contain status"
        print(f"✓ GET /api/moderator/help-requests/{request_id} returns request with {len(data.get('messages', []))} messages")
        return data
    
    def test_assign_manager_to_help_request(self):
        """POST /api/moderator/help-requests/{id}/assign assigns manager and changes status"""
        # Get pending requests
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        pending_requests = [r for r in requests_list if r.get("status") == "pending"]
        
        if not pending_requests:
            print("  No pending requests to assign, checking existing active request")
            active_requests = [r for r in requests_list if r.get("status") == "active"]
            if active_requests:
                print(f"✓ Found active request with assigned manager: {active_requests[0].get('assigned_manager_name')}")
                return
            pytest.skip("No pending or active help requests found")
        
        request_id = pending_requests[0]["id"]
        
        # Get available managers
        managers_response = requests.get(f"{BASE_URL}/api/moderator/available-managers", headers=self.headers)
        if managers_response.status_code != 200:
            pytest.skip("Could not get available managers")
        
        managers = managers_response.json()
        if not managers:
            pytest.skip("No available managers")
        
        manager_id = managers[0]["id"]
        
        # Assign manager
        response = requests.post(
            f"{BASE_URL}/api/moderator/help-requests/{request_id}/assign",
            json={"manager_id": manager_id},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "manager_name" in data, "Response should contain manager_name"
        print(f"✓ POST /api/moderator/help-requests/{request_id}/assign assigned manager: {data['manager_name']}")
        
        # Verify status changed to active
        verify_response = requests.get(f"{BASE_URL}/api/moderator/help-requests/{request_id}", headers=self.headers)
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            assert verify_data.get("status") == "active", f"Status should be 'active', got {verify_data.get('status')}"
            assert verify_data.get("assigned_manager_id") == manager_id, "Manager ID should match"
            print("✓ Request status changed to 'active' and manager assigned")
    
    def test_send_message_as_moderator(self):
        """POST /api/moderator/help-requests/{id}/messages sends manager message"""
        # Get active requests
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        active_requests = [r for r in requests_list if r.get("status") == "active"]
        
        if not active_requests:
            # Use any request
            if not requests_list:
                pytest.skip("No help requests found")
            request_id = requests_list[0]["id"]
        else:
            request_id = active_requests[0]["id"]
        
        test_message = f"TEST_manager_message_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/moderator/help-requests/{request_id}/messages",
            json={"content": test_message},
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "message_data" in data, "Response should contain message_data"
        
        msg_data = data["message_data"]
        assert msg_data.get("sender_type") == "manager", "Sender type should be 'manager'"
        assert msg_data.get("content") == test_message, "Content should match"
        print(f"✓ POST /api/moderator/help-requests/{request_id}/messages sent manager message")
    
    def test_close_help_request(self):
        """POST /api/moderator/help-requests/{id}/close closes the request"""
        # Get active requests
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200:
            pytest.skip("Could not get help requests list")
        
        requests_list = list_response.json()
        
        # Find a request that can be closed (not already closed)
        closeable = [r for r in requests_list if r.get("status") != "closed"]
        
        if not closeable:
            print("  All requests already closed, checking close endpoint works")
            if requests_list:
                request_id = requests_list[0]["id"]
                response = requests.post(
                    f"{BASE_URL}/api/moderator/help-requests/{request_id}/close",
                    headers=self.headers
                )
                # Should still return 200 even if already closed
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                print("✓ Close endpoint works (request was already closed)")
            return
        
        request_id = closeable[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/moderator/help-requests/{request_id}/close",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"✓ POST /api/moderator/help-requests/{request_id}/close closed request")
        
        # Verify status changed
        verify_response = requests.get(f"{BASE_URL}/api/moderator/help-requests/{request_id}", headers=self.headers)
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            assert verify_data.get("status") == "closed", f"Status should be 'closed', got {verify_data.get('status')}"
            print("✓ Request status changed to 'closed'")


class TestHelpRequestsErrorHandling:
    """Test error handling for help request endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_get_nonexistent_help_request(self):
        """GET /api/moderator/help-requests/{id} returns 404 for nonexistent request"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/moderator/help-requests/{fake_id}", headers=self.headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ GET nonexistent help request returns 404")
    
    def test_assign_without_manager_id(self):
        """POST /api/moderator/help-requests/{id}/assign returns 400 without manager_id"""
        # Get any request
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No help requests available")
        
        request_id = list_response.json()[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/moderator/help-requests/{request_id}/assign",
            json={},  # No manager_id
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Assign without manager_id returns 400")
    
    def test_assign_nonexistent_manager(self):
        """POST /api/moderator/help-requests/{id}/assign returns 404 for nonexistent manager"""
        # Get any request
        list_response = requests.get(f"{BASE_URL}/api/moderator/help-requests", headers=self.headers)
        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No help requests available")
        
        request_id = list_response.json()[0]["id"]
        fake_manager_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/moderator/help-requests/{request_id}/assign",
            json={"manager_id": fake_manager_id},
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Assign nonexistent manager returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
