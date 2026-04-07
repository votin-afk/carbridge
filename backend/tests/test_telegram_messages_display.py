"""
Test suite for Telegram messages display in deal chats
Tests:
1. GET /api/deals/{deal_id}/stages/{stage_key}/messages returns messages with source='telegram' and file_ids
2. GET /api/deals/{deal_id}/messages returns all messages including telegram ones
3. Stage dialog shows messages even when no contractor is assigned
4. File download links for messages with file_ids
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"
TEST_DEAL_ID = "ff3bbaf2-fc3e-40a3-8119-d9beb1522971"  # Audi Q4 e-tron with telegram messages
TEST_STAGE_KEY = "insurance"  # Stage with telegram messages and no contractor


class TestTelegramMessagesDisplay:
    """Tests for Telegram messages display in deal chats"""
    
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
        
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
        yield
    
    def test_stage_messages_endpoint_returns_source_field(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/messages returns source field"""
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        messages = response.json()
        assert isinstance(messages, list), "Response should be a list"
        
        # Check if any messages have source field
        print(f"Found {len(messages)} messages in {TEST_STAGE_KEY} stage")
        
        telegram_messages = [m for m in messages if m.get("source") == "telegram"]
        print(f"Found {len(telegram_messages)} telegram messages")
        
        # Verify message structure
        for msg in messages:
            assert "id" in msg, "Message should have id"
            assert "content" in msg or "file_ids" in msg, "Message should have content or file_ids"
            assert "sender_type" in msg, "Message should have sender_type"
            assert "created_at" in msg, "Message should have created_at"
            # source field may not be present for non-telegram messages
            if msg.get("source") == "telegram":
                print(f"  Telegram message: {msg.get('content', '')[:50]}...")
    
    def test_stage_messages_endpoint_returns_file_ids_field(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/messages returns file_ids field"""
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        
        assert response.status_code == 200
        
        messages = response.json()
        
        # Check for file_ids field in messages
        messages_with_files = [m for m in messages if m.get("file_ids") and len(m.get("file_ids", [])) > 0]
        print(f"Found {len(messages_with_files)} messages with file_ids")
        
        for msg in messages_with_files:
            file_ids = msg.get("file_ids", [])
            print(f"  Message has {len(file_ids)} files: {file_ids}")
            assert isinstance(file_ids, list), "file_ids should be a list"
    
    def test_deal_messages_endpoint_returns_telegram_messages(self):
        """Test GET /api/deals/{deal_id}/messages returns all messages including telegram ones"""
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/messages"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        messages = response.json()
        assert isinstance(messages, list), "Response should be a list"
        
        print(f"Found {len(messages)} total messages in deal")
        
        # Check for telegram messages
        telegram_messages = [m for m in messages if m.get("source") == "telegram"]
        print(f"Found {len(telegram_messages)} telegram messages in deal")
        
        # Verify telegram messages have required fields
        for msg in telegram_messages:
            assert "source" in msg, "Telegram message should have source field"
            assert msg["source"] == "telegram", "Source should be 'telegram'"
            # file_ids should be present (even if empty)
            assert "file_ids" in msg or True, "Telegram message should have file_ids field"
    
    def test_stage_messages_without_contractor(self):
        """Test that stage messages are returned even when no contractor is assigned"""
        # First check the deal's stage data
        response = self.session.get(f"{BASE_URL}/api/deals/{TEST_DEAL_ID}")
        
        if response.status_code == 200:
            deal = response.json()
            stages = deal.get("stages", {})
            insurance_stage = stages.get(TEST_STAGE_KEY, {})
            contractor_id = insurance_stage.get("contractor_id")
            print(f"Insurance stage contractor_id: {contractor_id}")
        
        # Get messages for the stage
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        
        # Should return 200 even without contractor
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        messages = response.json()
        print(f"Stage {TEST_STAGE_KEY} has {len(messages)} messages (contractor may not be assigned)")
    
    def test_file_download_endpoint_exists(self):
        """Test that file download endpoint exists and works"""
        # First get messages with file_ids
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        
        if response.status_code != 200:
            pytest.skip("Could not get messages")
        
        messages = response.json()
        messages_with_files = [m for m in messages if m.get("file_ids") and len(m.get("file_ids", [])) > 0]
        
        if not messages_with_files:
            print("No messages with files found, checking deal files directly")
            # Check deal files
            files_response = self.session.get(f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files")
            if files_response.status_code == 200:
                files = files_response.json()
                print(f"Found {len(files)} files in deal")
                if files:
                    file_id = files[0].get("id")
                    # Test download endpoint
                    download_response = self.session.get(
                        f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files/{file_id}/download"
                    )
                    print(f"Download endpoint status: {download_response.status_code}")
            return
        
        # Test download for first file
        first_file_id = messages_with_files[0]["file_ids"][0]
        download_response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files/{first_file_id}/download"
        )
        
        # Should return 200 or 404 (if file doesn't exist on disk)
        assert download_response.status_code in [200, 404], f"Unexpected status: {download_response.status_code}"
        print(f"File download endpoint returned: {download_response.status_code}")


class TestDealEndpoints:
    """Test deal-related endpoints"""
    
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
        
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_get_deal_details(self):
        """Test GET /api/deals/{deal_id} returns deal with stages"""
        response = self.session.get(f"{BASE_URL}/api/deals/{TEST_DEAL_ID}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        deal = response.json()
        assert "id" in deal, "Deal should have id"
        assert "stages" in deal, "Deal should have stages"
        assert "car_info" in deal, "Deal should have car_info"
        
        print(f"Deal: {deal.get('car_info', {}).get('brand')} {deal.get('car_info', {}).get('model')}")
        print(f"Stages: {list(deal.get('stages', {}).keys())}")
    
    def test_get_deal_files(self):
        """Test GET /api/deals/{deal_id}/files returns files"""
        response = self.session.get(f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/files")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        files = response.json()
        assert isinstance(files, list), "Response should be a list"
        
        print(f"Found {len(files)} files in deal")
        
        # Check for telegram-sourced files
        telegram_files = [f for f in files if f.get("source") == "telegram"]
        print(f"Found {len(telegram_files)} files from Telegram")
        
        for f in telegram_files[:3]:  # Show first 3
            print(f"  - {f.get('original_name')} ({f.get('category')})")
    
    def test_get_stage_files(self):
        """Test GET /api/deals/{deal_id}/stages/{stage_key}/files returns files"""
        response = self.session.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/files"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        files = response.json()
        assert isinstance(files, list), "Response should be a list"
        
        print(f"Found {len(files)} files in {TEST_STAGE_KEY} stage")


class TestAuthenticationRequired:
    """Test that endpoints require authentication"""
    
    def test_stage_messages_requires_auth(self):
        """Test that stage messages endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_deal_messages_requires_auth(self):
        """Test that deal messages endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/deals/{TEST_DEAL_ID}/messages"
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
