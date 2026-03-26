"""
Test suite for Moderator Stage Features:
- GET /api/moderator/deals/{deal_id}/stages/{stage_key}/files - returns files for the stage
- GET /api/moderator/deals/{deal_id}/files/{file_id}/download - returns file content
- GET /api/moderator/deals/{deal_id}/stages/{stage_key}/messages - returns messages including moderator messages
- POST /api/moderator/deals/{deal_id}/stages/{stage_key}/messages - creates a moderator message
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"

# Known test data from previous iterations
TEST_DEAL_ID = "c650aaba-5356-4e97-8cee-133e920c3f03"
TEST_STAGE_KEY = "inspection"
TEST_FILE_ID = "43164680-e0da-4f53-a8ff-7559d7209f72"  # JPG file


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """Headers with authorization"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestModeratorStageFiles:
    """Tests for GET /api/moderator/deals/{deal_id}/stages/{stage_key}/files"""
    
    def test_get_stage_files_success(self, auth_headers):
        """Test getting files for a stage returns list of files"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/files",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        files = response.json()
        assert isinstance(files, list)
        assert len(files) >= 1, "Expected at least 1 file in inspection stage"
        
        # Verify file structure
        for file in files:
            assert "id" in file
            assert "deal_id" in file
            assert "stage_key" in file
            assert "original_name" in file
            assert "mime_type" in file
            assert "size" in file
            assert "category" in file
            assert "uploader_name" in file
            assert "created_at" in file
    
    def test_get_stage_files_has_image(self, auth_headers):
        """Test that stage files include image with category='photo'"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/files",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        files = response.json()
        photo_files = [f for f in files if f.get("category") == "photo"]
        assert len(photo_files) >= 1, "Expected at least 1 photo file"
        
        # Verify photo has image mime type
        for photo in photo_files:
            assert photo["mime_type"].startswith("image/"), f"Photo should have image mime type, got {photo['mime_type']}"
    
    def test_get_stage_files_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/files"
        )
        assert response.status_code in [401, 403]
    
    def test_get_stage_files_nonexistent_deal(self, auth_headers):
        """Test 404 for nonexistent deal"""
        fake_deal_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{fake_deal_id}/stages/{TEST_STAGE_KEY}/files",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestModeratorFileDownload:
    """Tests for GET /api/moderator/deals/{deal_id}/files/{file_id}/download"""
    
    def test_download_file_success(self, auth_headers):
        """Test downloading a file returns file content"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/files/{TEST_FILE_ID}/download",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify content type is image
        content_type = response.headers.get("content-type", "")
        assert "image" in content_type, f"Expected image content type, got {content_type}"
        
        # Verify content is not empty
        assert len(response.content) > 0, "File content should not be empty"
    
    def test_download_file_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/files/{TEST_FILE_ID}/download"
        )
        assert response.status_code in [401, 403]
    
    def test_download_nonexistent_file(self, auth_headers):
        """Test 404 for nonexistent file"""
        fake_file_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/files/{fake_file_id}/download",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestModeratorStageMessages:
    """Tests for GET /api/moderator/deals/{deal_id}/stages/{stage_key}/messages"""
    
    def test_get_stage_messages_success(self, auth_headers):
        """Test getting messages for a stage returns list of messages"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        messages = response.json()
        assert isinstance(messages, list)
        assert len(messages) >= 1, "Expected at least 1 message in inspection stage"
        
        # Verify message structure
        for msg in messages:
            assert "id" in msg
            assert "deal_id" in msg
            assert "stage_key" in msg
            assert "sender_name" in msg
            assert "sender_type" in msg
            assert "content" in msg
            assert "created_at" in msg
    
    def test_get_stage_messages_includes_moderator_messages(self, auth_headers):
        """Test that messages include moderator type messages"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        messages = response.json()
        moderator_messages = [m for m in messages if m.get("sender_type") == "moderator"]
        
        # There should be at least one moderator message (we created one in previous tests)
        assert len(moderator_messages) >= 1, "Expected at least 1 moderator message"
        
        # Verify moderator message has correct structure
        for msg in moderator_messages:
            assert msg["sender_type"] == "moderator"
            assert "source" in msg
    
    def test_get_stage_messages_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages"
        )
        assert response.status_code in [401, 403]
    
    def test_get_stage_messages_nonexistent_deal(self, auth_headers):
        """Test 404 for nonexistent deal"""
        fake_deal_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{fake_deal_id}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestModeratorSendStageMessage:
    """Tests for POST /api/moderator/deals/{deal_id}/stages/{stage_key}/messages"""
    
    def test_send_moderator_message_success(self, auth_headers):
        """Test sending a moderator message to stage chat"""
        test_content = f"TEST_Moderator message {uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers,
            json={"content": test_content}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data or "id" in data
        
        # Verify message was created by fetching messages
        messages_response = requests.get(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers
        )
        assert messages_response.status_code == 200
        
        messages = messages_response.json()
        matching_messages = [m for m in messages if m.get("content") == test_content]
        assert len(matching_messages) >= 1, "Sent message should appear in messages list"
        
        # Verify message has moderator sender_type
        sent_msg = matching_messages[0]
        assert sent_msg["sender_type"] == "moderator"
        assert sent_msg["source"] == "platform"
    
    def test_send_empty_message_fails(self, auth_headers):
        """Test that empty message returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers,
            json={"content": ""}
        )
        assert response.status_code == 400
    
    def test_send_whitespace_message_fails(self, auth_headers):
        """Test that whitespace-only message returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers,
            json={"content": "   "}
        )
        assert response.status_code == 400
    
    def test_send_message_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/moderator/deals/{TEST_DEAL_ID}/stages/{TEST_STAGE_KEY}/messages",
            json={"content": "Test message"}
        )
        assert response.status_code in [401, 403]
    
    def test_send_message_nonexistent_deal(self, auth_headers):
        """Test 404 for nonexistent deal"""
        fake_deal_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/moderator/deals/{fake_deal_id}/stages/{TEST_STAGE_KEY}/messages",
            headers=auth_headers,
            json={"content": "Test message"}
        )
        assert response.status_code == 404


class TestPendingStagesEndpoint:
    """Tests for GET /api/moderator/deals/pending-stages"""
    
    def test_get_pending_stages_success(self, auth_headers):
        """Test getting pending stages returns list"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/pending-stages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        stages = response.json()
        assert isinstance(stages, list)
        
        # If there are pending stages, verify structure
        if len(stages) > 0:
            stage = stages[0]
            assert "deal_id" in stage
            assert "stage_key" in stage
            assert "car_info" in stage
            assert "contractor_name" in stage
    
    def test_get_pending_stages_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/moderator/deals/pending-stages"
        )
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
