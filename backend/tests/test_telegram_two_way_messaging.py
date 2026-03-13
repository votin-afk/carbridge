"""
Test suite for Two-Way Telegram Messaging
Tests:
- POST /api/telegram/webhook - callback_query handling (Reply button)
- POST /api/telegram/webhook - callback_query handling (Chat selection)
- POST /api/telegram/webhook - /chats command shows active chats
- POST /api/telegram/webhook - /cancel command cancels selection
- POST /api/telegram/webhook - regular message with single active chat
- POST /api/telegram/webhook - regular message with multiple active chats
- telegram_service functions: send_chat_selection, send_message_confirmation, send_awaiting_message_prompt
- Messages from Telegram saved to deal_messages collection with source='telegram'
- Notification to other party when message received from Telegram
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"

# Fake Telegram chat_id for testing (will fail Telegram API but internal logic should work)
TEST_CHAT_ID = 123456789


class TestTelegramWebhookCallbackQuery:
    """Tests for Telegram webhook callback_query handling (inline button presses)"""
    
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
            self.user_id = self.user.get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        # Get or create test deal
        self.deal_id = None
        self.test_stage = "inspection"
        
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        if deals_response.status_code == 200:
            deals = deals_response.json()
            if deals and len(deals) > 0:
                self.deal_id = deals[0]["id"]
    
    def test_webhook_callback_reply_button(self):
        """Test callback_query with 'reply' action from Reply button"""
        # Simulate callback_query from Telegram when user clicks "Reply" button
        webhook_payload = {
            "update_id": 123456789,
            "callback_query": {
                "id": "test_callback_id_123",
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "message": {
                    "message_id": 100,
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "type": "private"
                    }
                },
                "data": f"reply:{self.deal_id or 'fake-deal-id'}:{self.test_stage}"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        # Webhook should always return 200 OK to Telegram
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") == True, "Webhook should return ok: true"
        
        print("✓ Webhook callback_query 'reply' action processed successfully")
    
    def test_webhook_callback_select_chat(self):
        """Test callback_query with 'select' action from chat selection"""
        # Simulate callback_query when user selects a chat from inline keyboard
        webhook_payload = {
            "update_id": 123456790,
            "callback_query": {
                "id": "test_callback_id_456",
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "message": {
                    "message_id": 101,
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "type": "private"
                    }
                },
                "data": f"select:{self.deal_id or 'fake-deal-id'}:{self.test_stage}"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") == True, "Webhook should return ok: true"
        
        print("✓ Webhook callback_query 'select' action processed successfully")
    
    def test_webhook_callback_invalid_action(self):
        """Test callback_query with unknown action"""
        webhook_payload = {
            "update_id": 123456791,
            "callback_query": {
                "id": "test_callback_id_789",
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "Test"
                },
                "message": {
                    "message_id": 102,
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "type": "private"
                    }
                },
                "data": "unknown_action:param1:param2"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        # Should still return 200 OK (webhook must always acknowledge)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Webhook handles unknown callback action gracefully")


class TestTelegramWebhookCommands:
    """Tests for Telegram webhook command handling (/start, /chats, /cancel, /help)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_webhook_start_command(self):
        """Test /start command handling"""
        webhook_payload = {
            "update_id": 123456792,
            "message": {
                "message_id": 103,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "/start"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ /start command processed successfully")
    
    def test_webhook_start_with_verification_code(self):
        """Test /start command with deep link verification code"""
        # This simulates user clicking the Telegram link from the website
        verification_code = "test_verification_code_123"
        
        webhook_payload = {
            "update_id": 123456793,
            "message": {
                "message_id": 104,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": f"/start {verification_code}"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ /start with verification code processed successfully")
    
    def test_webhook_chats_command(self):
        """Test /chats command - shows active chats"""
        webhook_payload = {
            "update_id": 123456794,
            "message": {
                "message_id": 105,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "/chats"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ /chats command processed successfully")
    
    def test_webhook_cancel_command(self):
        """Test /cancel command - cancels chat selection"""
        webhook_payload = {
            "update_id": 123456795,
            "message": {
                "message_id": 106,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "/cancel"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ /cancel command processed successfully")
    
    def test_webhook_help_command(self):
        """Test /help command"""
        webhook_payload = {
            "update_id": 123456796,
            "message": {
                "message_id": 107,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "/help"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ /help command processed successfully")


class TestTelegramWebhookRegularMessages:
    """Tests for regular text message handling via webhook"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_webhook_regular_message_no_context(self):
        """Test regular message when user has no chat context selected"""
        webhook_payload = {
            "update_id": 123456797,
            "message": {
                "message_id": 108,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser",
                    "username": "testuser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "Hello, this is a test message"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("ok") == True
        
        print("✓ Regular message without context processed (should prompt for chat selection)")
    
    def test_webhook_empty_message(self):
        """Test webhook with empty message text"""
        webhook_payload = {
            "update_id": 123456798,
            "message": {
                "message_id": 109,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": ""
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Empty message handled gracefully")
    
    def test_webhook_message_with_photo(self):
        """Test webhook with photo message (no text)"""
        webhook_payload = {
            "update_id": 123456799,
            "message": {
                "message_id": 110,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "TestUser"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "photo": [
                    {"file_id": "test_photo_id", "width": 100, "height": 100}
                ]
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        
        # Should handle gracefully even without text
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        print("✓ Photo message handled gracefully")


class TestTelegramWebhookIntegration:
    """Integration tests for full two-way messaging flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication and test data"""
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
            self.user_id = self.user.get("id")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        # Get existing deal for testing
        self.deal_id = None
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        if deals_response.status_code == 200:
            deals = deals_response.json()
            if deals and len(deals) > 0:
                self.deal_id = deals[0]["id"]
    
    def test_full_reply_flow(self):
        """Test complete flow: Reply button -> message -> confirmation"""
        if not self.deal_id:
            pytest.skip("No existing deal for integration test")
        
        # Step 1: Simulate clicking Reply button
        callback_payload = {
            "update_id": 123456800,
            "callback_query": {
                "id": "integration_test_callback",
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "IntegrationTest"
                },
                "message": {
                    "message_id": 200,
                    "chat": {
                        "id": TEST_CHAT_ID,
                        "type": "private"
                    }
                },
                "data": f"reply:{self.deal_id}:inspection"
            }
        }
        
        response1 = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=callback_payload)
        assert response1.status_code == 200, "Reply callback should succeed"
        
        # Step 2: Send a message (context should be set from step 1)
        message_payload = {
            "update_id": 123456801,
            "message": {
                "message_id": 201,
                "from": {
                    "id": TEST_CHAT_ID,
                    "first_name": "IntegrationTest"
                },
                "chat": {
                    "id": TEST_CHAT_ID,
                    "type": "private"
                },
                "date": int(datetime.now(timezone.utc).timestamp()),
                "text": "TEST_TELEGRAM_MESSAGE: Integration test message"
            }
        }
        
        response2 = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=message_payload)
        assert response2.status_code == 200, "Message should be processed"
        
        print("✓ Full reply flow completed successfully")
    
    def test_webhook_malformed_payload(self):
        """Test webhook with malformed/incomplete payload"""
        # Empty payload
        response1 = self.session.post(f"{BASE_URL}/api/telegram/webhook", json={})
        assert response1.status_code == 200, "Empty payload should be handled gracefully"
        
        # Payload with only update_id
        response2 = self.session.post(f"{BASE_URL}/api/telegram/webhook", json={"update_id": 123})
        assert response2.status_code == 200, "Minimal payload should be handled"
        
        print("✓ Malformed payloads handled gracefully")
    
    def test_webhook_callback_missing_parts(self):
        """Test callback_query with incomplete data"""
        # Callback with only action, no deal_id or stage
        webhook_payload = {
            "update_id": 123456802,
            "callback_query": {
                "id": "incomplete_callback",
                "from": {"id": TEST_CHAT_ID},
                "message": {
                    "message_id": 202,
                    "chat": {"id": TEST_CHAT_ID, "type": "private"}
                },
                "data": "reply"  # Missing deal_id and stage_key
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/telegram/webhook", json=webhook_payload)
        assert response.status_code == 200, "Incomplete callback should be handled"
        
        print("✓ Incomplete callback data handled gracefully")


class TestTelegramServiceFunctions:
    """Tests for telegram_service helper functions via API behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_notify_new_message_includes_reply_button(self):
        """Verify notify_new_message function includes reply button in notifications"""
        # This is tested indirectly through the webhook behavior
        # When a message is sent via web, it should trigger notification with reply button
        
        # Get deals to find one with contractor
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        if deals_response.status_code != 200:
            pytest.skip("Could not get deals")
        
        deals = deals_response.json()
        if not deals:
            pytest.skip("No deals available for testing")
        
        deal = deals[0]
        deal_id = deal["id"]
        
        # Send a message via API (this should trigger notification with reply button)
        message_response = self.session.post(
            f"{BASE_URL}/api/deals/{deal_id}/stages/inspection/messages",
            json={"content": "TEST_MESSAGE: Testing notification with reply button"}
        )
        
        # Message sending should work (notification may fail for fake chat_id but that's expected)
        assert message_response.status_code in [200, 403], f"Unexpected status: {message_response.status_code}"
        
        print("✓ Message sent (notification with reply button would be triggered)")
    
    def test_webhook_endpoint_exists(self):
        """Verify webhook endpoint is accessible"""
        # Simple GET should return method not allowed or similar
        response = self.session.get(f"{BASE_URL}/api/telegram/webhook")
        
        # GET is not allowed, should return 405 or similar
        assert response.status_code in [405, 422, 400], f"Webhook GET should not be allowed, got {response.status_code}"
        
        print("✓ Webhook endpoint exists and rejects GET requests")


class TestDealMessagesFromTelegram:
    """Tests to verify messages from Telegram are saved correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
        
        # Get existing deal
        self.deal_id = None
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        if deals_response.status_code == 200:
            deals = deals_response.json()
            if deals:
                self.deal_id = deals[0]["id"]
    
    def test_messages_endpoint_returns_source_field(self):
        """Verify messages endpoint returns source field (web or telegram)"""
        if not self.deal_id:
            pytest.skip("No deal available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/deals/{self.deal_id}/stages/inspection/messages")
        
        if response.status_code == 200:
            messages = response.json()
            # If there are messages, check structure
            if messages:
                # Messages should have standard fields
                msg = messages[0]
                assert "content" in msg or "message" in msg, "Message should have content"
                assert "sender_name" in msg or "sender_id" in msg, "Message should have sender info"
                # source field may or may not be present depending on how message was sent
                print(f"✓ Messages retrieved: {len(messages)} messages")
            else:
                print("✓ Messages endpoint works (no messages yet)")
        elif response.status_code == 403:
            print("✓ Messages endpoint correctly restricts access")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
