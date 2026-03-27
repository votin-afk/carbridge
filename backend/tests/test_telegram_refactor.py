"""
Test suite for Telegram routes refactoring validation
Tests that telegram routes extracted to /app/backend/routes/telegram.py work correctly
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"
CONTRACTOR_EMAIL = "horon4ik@icloud.com"
CONTRACTOR_PASSWORD = "test123"


class TestCoreAPIs:
    """Test core platform APIs still work after refactoring"""
    
    def test_health_endpoint(self):
        """GET /api/health should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ GET /api/health - 200 OK")
    
    def test_catalog_brands(self):
        """GET /api/catalog/brands should return brands list"""
        response = requests.get(f"{BASE_URL}/api/catalog/brands")
        assert response.status_code == 200, f"Catalog brands failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Brands should be a list"
        print(f"✓ GET /api/catalog/brands - 200 OK, {len(data)} brands")
    
    def test_deals_endpoint_requires_auth(self):
        """GET /api/deals should require authentication"""
        response = requests.get(f"{BASE_URL}/api/deals")
        assert response.status_code in [401, 403], f"Deals should require auth: {response.status_code}"
        print("✓ GET /api/deals - requires auth (401/403)")
    
    def test_garage_endpoint_requires_auth(self):
        """GET /api/garage should require authentication"""
        response = requests.get(f"{BASE_URL}/api/garage")
        assert response.status_code in [401, 403], f"Garage should require auth: {response.status_code}"
        print("✓ GET /api/garage - requires auth (401/403)")


class TestUserTelegramEndpoints:
    """Test user Telegram linking endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_telegram_status_requires_auth(self):
        """GET /api/telegram/status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/telegram/status")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ GET /api/telegram/status - requires auth")
    
    def test_telegram_status_with_auth(self, admin_token):
        """GET /api/telegram/status should return status with auth"""
        response = requests.get(
            f"{BASE_URL}/api/telegram/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Status failed: {response.text}"
        data = response.json()
        assert "linked" in data, "Response should have 'linked' field"
        print(f"✓ GET /api/telegram/status - 200 OK, linked={data.get('linked')}")
    
    def test_telegram_link_requires_auth(self):
        """POST /api/telegram/link should require authentication"""
        response = requests.post(f"{BASE_URL}/api/telegram/link")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ POST /api/telegram/link - requires auth")
    
    def test_telegram_link_with_auth(self, admin_token):
        """POST /api/telegram/link should return link with auth"""
        response = requests.post(
            f"{BASE_URL}/api/telegram/link",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Link failed: {response.text}"
        data = response.json()
        assert "link" in data, "Response should have 'link' field"
        assert "bot_username" in data, "Response should have 'bot_username' field"
        assert "t.me" in data["link"], "Link should be a Telegram link"
        print(f"✓ POST /api/telegram/link - 200 OK, bot=@{data.get('bot_username')}")
    
    def test_telegram_unlink_requires_auth(self):
        """POST /api/telegram/unlink should require authentication"""
        response = requests.post(f"{BASE_URL}/api/telegram/unlink")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ POST /api/telegram/unlink - requires auth")
    
    def test_telegram_test_requires_auth(self):
        """POST /api/telegram/test should require authentication"""
        response = requests.post(f"{BASE_URL}/api/telegram/test")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ POST /api/telegram/test - requires auth")


class TestContractorTelegramEndpoints:
    """Test contractor Telegram linking endpoints"""
    
    @pytest.fixture
    def contractor_token(self):
        """Get contractor auth token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Contractor login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_contractor_telegram_status_requires_auth(self):
        """GET /api/contractor/telegram/status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/contractor/telegram/status")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ GET /api/contractor/telegram/status - requires auth")
    
    def test_contractor_telegram_status_with_auth(self, contractor_token):
        """GET /api/contractor/telegram/status should return status with auth"""
        response = requests.get(
            f"{BASE_URL}/api/contractor/telegram/status",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200, f"Status failed: {response.text}"
        data = response.json()
        assert "linked" in data, "Response should have 'linked' field"
        print(f"✓ GET /api/contractor/telegram/status - 200 OK, linked={data.get('linked')}")
    
    def test_contractor_telegram_link_requires_auth(self):
        """POST /api/contractor/telegram/link should require authentication"""
        response = requests.post(f"{BASE_URL}/api/contractor/telegram/link")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ POST /api/contractor/telegram/link - requires auth")
    
    def test_contractor_telegram_link_with_auth(self, contractor_token):
        """POST /api/contractor/telegram/link should return link with auth"""
        response = requests.post(
            f"{BASE_URL}/api/contractor/telegram/link",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200, f"Link failed: {response.text}"
        data = response.json()
        assert "link" in data, "Response should have 'link' field"
        assert "bot_username" in data, "Response should have 'bot_username' field"
        assert "t.me" in data["link"], "Link should be a Telegram link"
        print(f"✓ POST /api/contractor/telegram/link - 200 OK, bot=@{data.get('bot_username')}")
    
    def test_contractor_telegram_unlink_requires_auth(self):
        """POST /api/contractor/telegram/unlink should require authentication"""
        response = requests.post(f"{BASE_URL}/api/contractor/telegram/unlink")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ POST /api/contractor/telegram/unlink - requires auth")


class TestAdminTelegramEndpoints:
    """Test admin Telegram stats endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_admin_telegram_stats_requires_auth(self):
        """GET /api/admin/telegram/stats should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/telegram/stats")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ GET /api/admin/telegram/stats - requires auth")
    
    def test_admin_telegram_stats_with_auth(self, admin_token):
        """GET /api/admin/telegram/stats should return stats with admin auth"""
        response = requests.get(
            f"{BASE_URL}/api/admin/telegram/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        assert "users" in data, "Response should have 'users' field"
        assert "contractors" in data, "Response should have 'contractors' field"
        assert "total" in data["users"], "Users should have 'total' field"
        assert "linked" in data["users"], "Users should have 'linked' field"
        print(f"✓ GET /api/admin/telegram/stats - 200 OK, users={data['users']['total']}, linked={data['users']['linked']}")


class TestContractorDashboard:
    """Test contractor dashboard endpoints"""
    
    @pytest.fixture
    def contractor_token(self):
        """Get contractor auth token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Contractor login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_contractor_dashboard_requires_auth(self):
        """GET /api/contractor-dashboard should require authentication"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ GET /api/contractor-dashboard - requires auth")
    
    def test_contractor_dashboard_with_auth(self, contractor_token):
        """GET /api/contractor-dashboard should return dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        assert "contractor" in data, "Response should have 'contractor' field"
        print(f"✓ GET /api/contractor-dashboard - 200 OK, contractor={data.get('contractor', {}).get('company_name')}")
    
    def test_contractor_profile_requires_auth(self):
        """GET /api/contractor/profile should require authentication"""
        response = requests.get(f"{BASE_URL}/api/contractor/profile")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print("✓ GET /api/contractor/profile - requires auth")
    
    def test_contractor_profile_with_auth(self, contractor_token):
        """GET /api/contractor/profile should return profile data"""
        response = requests.get(
            f"{BASE_URL}/api/contractor/profile",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200, f"Profile failed: {response.text}"
        data = response.json()
        # Profile returns about, city, address, certificates etc.
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ GET /api/contractor/profile - 200 OK, keys={list(data.keys())[:5]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
