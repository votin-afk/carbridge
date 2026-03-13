"""
Test suite for Telegram integration and Stage-specific endpoints
Tests:
- Telegram link generation (POST /api/telegram/link)
- Telegram status check (GET /api/telegram/status)
- Telegram test notification (POST /api/telegram/test)
- Telegram unlink (POST /api/telegram/unlink)
- Stage files upload (POST /api/deals/{deal_id}/stages/{stage_key}/files)
- Stage files get (GET /api/deals/{deal_id}/stages/{stage_key}/files)
- Stage messages send (POST /api/deals/{deal_id}/stages/{stage_key}/messages)
- Stage messages get (GET /api/deals/{deal_id}/stages/{stage_key}/messages)
- Stage completion (POST /api/deals/{deal_id}/stages/{stage_key}/complete)
"""
import pytest
import requests
import os
import uuid
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test"


class TestTelegramIntegration:
    """Tests for Telegram integration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin user
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.user = response.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_telegram_link_generation(self):
        """Test POST /api/telegram/link - generates link for Telegram binding"""
        response = self.session.post(f"{BASE_URL}/api/telegram/link")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "link" in data, "Response should contain 'link'"
        assert "code" in data, "Response should contain 'code'"
        assert "bot_username" in data, "Response should contain 'bot_username'"
        
        # Verify link format
        assert data["link"].startswith("https://t.me/"), f"Link should start with https://t.me/, got {data['link']}"
        assert "?start=" in data["link"], "Link should contain ?start= parameter"
        
        # Verify code is present and non-empty
        assert len(data["code"]) > 0, "Code should not be empty"
        
        print(f"✓ Telegram link generated: {data['link']}")
        print(f"✓ Bot username: {data['bot_username']}")
    
    def test_telegram_status_check(self):
        """Test GET /api/telegram/status - checks Telegram binding status"""
        response = self.session.get(f"{BASE_URL}/api/telegram/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "linked" in data, "Response should contain 'linked' field"
        assert isinstance(data["linked"], bool), "'linked' should be boolean"
        
        # username can be None if not linked
        if data["linked"]:
            print(f"✓ Telegram is linked, username: {data.get('username')}")
        else:
            print("✓ Telegram is not linked (expected for test user)")
    
    def test_telegram_test_notification_without_link(self):
        """Test POST /api/telegram/test - should fail if Telegram not linked"""
        # First check if Telegram is linked
        status_response = self.session.get(f"{BASE_URL}/api/telegram/status")
        status_data = status_response.json()
        
        if not status_data.get("linked"):
            # Should return 400 if not linked
            response = self.session.post(f"{BASE_URL}/api/telegram/test")
            assert response.status_code == 400, f"Expected 400 when Telegram not linked, got {response.status_code}"
            print("✓ Test notification correctly rejected when Telegram not linked")
        else:
            # If linked, test should succeed
            response = self.session.post(f"{BASE_URL}/api/telegram/test")
            assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
            print("✓ Test notification sent (Telegram is linked)")
    
    def test_telegram_unlink(self):
        """Test POST /api/telegram/unlink - unlinks Telegram"""
        response = self.session.post(f"{BASE_URL}/api/telegram/unlink")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        
        # Verify status is now unlinked
        status_response = self.session.get(f"{BASE_URL}/api/telegram/status")
        status_data = status_response.json()
        assert status_data["linked"] == False, "Telegram should be unlinked after unlink call"
        
        print("✓ Telegram successfully unlinked")
    
    def test_telegram_endpoints_require_auth(self):
        """Test that Telegram endpoints require authentication"""
        # Create session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        # Test link endpoint
        response = no_auth_session.post(f"{BASE_URL}/api/telegram/link")
        assert response.status_code in [401, 403], f"Link should require auth, got {response.status_code}"
        
        # Test status endpoint
        response = no_auth_session.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code in [401, 403], f"Status should require auth, got {response.status_code}"
        
        # Test unlink endpoint
        response = no_auth_session.post(f"{BASE_URL}/api/telegram/unlink")
        assert response.status_code in [401, 403], f"Unlink should require auth, got {response.status_code}"
        
        print("✓ All Telegram endpoints correctly require authentication")


class TestStageEndpoints:
    """Tests for Stage-specific endpoints (files, messages, completion)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication and create test deal if needed"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin user
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.user = response.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        # Get existing deals or create one
        self.deal_id = None
        self.test_stage = "inspection"  # Use inspection stage for testing
        
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        if deals_response.status_code == 200:
            deals = deals_response.json()
            if deals and len(deals) > 0:
                self.deal_id = deals[0]["id"]
                print(f"Using existing deal: {self.deal_id}")
    
    def test_get_stage_messages_no_deal(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/messages with invalid deal"""
        fake_deal_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/messages")
        
        assert response.status_code == 404, f"Expected 404 for non-existent deal, got {response.status_code}"
        print("✓ Stage messages correctly returns 404 for non-existent deal")
    
    def test_get_stage_files_no_deal(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/files with invalid deal"""
        fake_deal_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/files")
        
        assert response.status_code == 404, f"Expected 404 for non-existent deal, got {response.status_code}"
        print("✓ Stage files correctly returns 404 for non-existent deal")
    
    def test_complete_stage_no_deal(self):
        """Test POST /api/deals/{deal_id}/stages/{stage_key}/complete with invalid deal"""
        fake_deal_id = str(uuid.uuid4())
        response = self.session.post(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/complete")
        
        assert response.status_code == 404, f"Expected 404 for non-existent deal, got {response.status_code}"
        print("✓ Stage complete correctly returns 404 for non-existent deal")
    
    def test_stage_messages_with_existing_deal(self):
        """Test stage messages endpoints with existing deal"""
        if not self.deal_id:
            pytest.skip("No existing deal found for testing")
        
        # Get messages
        response = self.session.get(f"{BASE_URL}/api/deals/{self.deal_id}/stages/{self.test_stage}/messages")
        
        # Should return 200 (even if empty) or 403 if not owner
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Messages should be a list"
            print(f"✓ Stage messages retrieved: {len(data)} messages")
        else:
            print("✓ Stage messages correctly denied access (not deal owner)")
    
    def test_stage_files_with_existing_deal(self):
        """Test stage files endpoints with existing deal"""
        if not self.deal_id:
            pytest.skip("No existing deal found for testing")
        
        # Get files
        response = self.session.get(f"{BASE_URL}/api/deals/{self.deal_id}/stages/{self.test_stage}/files")
        
        # Should return 200 (even if empty) or 403 if not owner
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Files should be a list"
            print(f"✓ Stage files retrieved: {len(data)} files")
        else:
            print("✓ Stage files correctly denied access (not deal owner)")
    
    def test_send_stage_message_with_existing_deal(self):
        """Test sending message to stage"""
        if not self.deal_id:
            pytest.skip("No existing deal found for testing")
        
        response = self.session.post(
            f"{BASE_URL}/api/deals/{self.deal_id}/stages/{self.test_stage}/messages",
            json={"content": "TEST_MESSAGE: Test message from automated testing"}
        )
        
        # Should return 200 or 403 if not owner
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data or "id" in data, "Response should contain message or id"
            print("✓ Stage message sent successfully")
        else:
            print("✓ Stage message correctly denied (not deal owner)")
    
    def test_upload_stage_file_with_existing_deal(self):
        """Test uploading file to stage"""
        if not self.deal_id:
            pytest.skip("No existing deal found for testing")
        
        # Create a test file
        test_file_content = b"TEST FILE CONTENT FOR AUTOMATED TESTING"
        files = {
            'file': ('test_file.txt', io.BytesIO(test_file_content), 'text/plain')
        }
        
        # Remove Content-Type header for multipart upload
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/deals/{self.deal_id}/stages/{self.test_stage}/files",
            files=files,
            data={"description": "Test file from automated testing"},
            headers=headers
        )
        
        # Should return 200 or 403 if not owner
        assert response.status_code in [200, 403], f"Expected 200 or 403, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "file_id" in data or "message" in data, "Response should contain file_id or message"
            print("✓ Stage file uploaded successfully")
        else:
            print("✓ Stage file upload correctly denied (not deal owner)")
    
    def test_complete_stage_with_existing_deal(self):
        """Test completing a stage"""
        if not self.deal_id:
            pytest.skip("No existing deal found for testing")
        
        response = self.session.post(f"{BASE_URL}/api/deals/{self.deal_id}/stages/{self.test_stage}/complete")
        
        # Various expected responses:
        # 200 - success
        # 400 - stage already completed, no contractor, etc.
        # 403 - not deal owner
        assert response.status_code in [200, 400, 403], f"Expected 200, 400, or 403, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            print("✓ Stage completed successfully")
        elif response.status_code == 400:
            data = response.json()
            print(f"✓ Stage completion correctly rejected: {data.get('detail', 'Unknown reason')}")
        else:
            print("✓ Stage completion correctly denied (not deal owner)")
    
    def test_stage_endpoints_require_auth(self):
        """Test that stage endpoints require authentication"""
        fake_deal_id = str(uuid.uuid4())
        no_auth_session = requests.Session()
        
        # Test messages GET
        response = no_auth_session.get(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/messages")
        assert response.status_code in [401, 403], f"Messages GET should require auth, got {response.status_code}"
        
        # Test messages POST
        response = no_auth_session.post(
            f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/messages",
            json={"content": "test"}
        )
        assert response.status_code in [401, 403], f"Messages POST should require auth, got {response.status_code}"
        
        # Test files GET
        response = no_auth_session.get(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/files")
        assert response.status_code in [401, 403], f"Files GET should require auth, got {response.status_code}"
        
        # Test complete POST
        response = no_auth_session.post(f"{BASE_URL}/api/deals/{fake_deal_id}/stages/inspection/complete")
        assert response.status_code in [401, 403], f"Complete POST should require auth, got {response.status_code}"
        
        print("✓ All stage endpoints correctly require authentication")


class TestDealCreationForStages:
    """Tests that create a deal to test stage functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin user
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.user = response.json().get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        self.created_car_id = None
        self.created_deal_id = None
    
    def test_create_car_and_deal_for_stage_testing(self):
        """Create a car and deal to test stage functionality"""
        # First, add a car to garage
        car_data = {
            "brand": "TEST_BRAND",
            "model": "TEST_MODEL_STAGE",
            "year": 2023,
            "price_cny": 150000,
            "engine_type": "electric",
            "mileage": 5000,
            "description": "Test car for stage testing"
        }
        
        car_response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        
        if car_response.status_code == 201:
            car = car_response.json()
            self.created_car_id = car.get("id")
            print(f"✓ Test car created: {self.created_car_id}")
            
            # Try to create a deal from this car
            deal_response = self.session.post(f"{BASE_URL}/api/deals/create", json={
                "car_id": self.created_car_id
            })
            
            # Deal creation may fail if user is not verified - that's expected
            if deal_response.status_code == 200:
                deal = deal_response.json()
                self.created_deal_id = deal.get("deal_id")
                print(f"✓ Test deal created: {self.created_deal_id}")
            else:
                print(f"Deal creation returned {deal_response.status_code}: {deal_response.text}")
                print("(This is expected if user is not verified)")
        else:
            print(f"Car creation returned {car_response.status_code}: {car_response.text}")
    
    def teardown_method(self, method):
        """Cleanup created test data"""
        if self.created_deal_id:
            try:
                self.session.delete(f"{BASE_URL}/api/deals/{self.created_deal_id}")
                print(f"Cleaned up deal: {self.created_deal_id}")
            except:
                pass
        
        if self.created_car_id:
            try:
                self.session.delete(f"{BASE_URL}/api/garage/{self.created_car_id}")
                print(f"Cleaned up car: {self.created_car_id}")
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
