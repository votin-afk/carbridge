"""
Test suite for contractor offer features:
- POST /api/contractor-offers - create offer with car details
- POST /api/contractor-offers/{offer_id}/files - upload files
- GET /api/offers/{offer_id}/files - get offer files
- GET /api/offer-files/{file_id}/download - download file
- GET /api/contractors/{contractor_id}/public-profile - public profile
- GET /api/contractor-dashboard - no 'applications' field
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CONTRACTOR_EMAIL = "test.contractor@test.com"
CONTRACTOR_PASSWORD = "test123"
USER_EMAIL = "test@test.com"
USER_PASSWORD = "test"


class TestContractorAuth:
    """Test contractor authentication"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Contractor login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"User login failed: {response.status_code} - {response.text}")
    
    def test_contractor_login(self):
        """Test contractor can login"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "contractor" in data


class TestContractorDashboard:
    """Test contractor dashboard endpoint"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Contractor login failed")
    
    def test_dashboard_returns_data(self, contractor_token):
        """Test dashboard returns expected fields"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard", headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "contractor" in data
        assert "active_tenders" in data
        assert "my_offers" in data
        assert "completed_deals" in data
        assert "active_deals" in data
        assert "tenders" in data
        assert "recent_offers" in data
    
    def test_dashboard_no_applications_field(self, contractor_token):
        """Test dashboard does NOT return 'applications' field (removed feature)"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard", headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # 'applications' field should NOT be present
        assert "applications" not in data, "Dashboard should not have 'applications' field"
    
    def test_dashboard_contractor_info(self, contractor_token):
        """Test dashboard returns contractor info"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard", headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        contractor = data.get("contractor", {})
        assert "id" in contractor
        assert "company_name" in contractor
        assert "services" in contractor
        assert "rating" in contractor


class TestContractorOffers:
    """Test contractor offer creation with car details"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Contractor login failed")
    
    @pytest.fixture(scope="class")
    def active_tender_id(self, contractor_token):
        """Get an active tender ID"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard", headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        if response.status_code == 200:
            tenders = response.json().get("tenders", [])
            if tenders:
                return tenders[0]["id"]
        pytest.skip("No active tenders found")
    
    def test_create_offer_with_car_details(self, contractor_token, active_tender_id):
        """Test creating offer with all car detail fields"""
        offer_data = {
            "tender_id": active_tender_id,
            "price_usd": 25000,
            "price_cny": 180000,
            "delivery_days": 30,
            "delivery_cost": 500,
            "car_brand": "BYD",
            "car_model": "Han EV",
            "car_year": "2024",
            "car_mileage": "15000",
            "car_engine_type": "electric",
            "car_engine_volume": "",
            "car_color": "Чёрный",
            "car_transmission": "automatic",
            "car_vin": "LGXC12345678901234",
            "car_details": "Отличное состояние, полная комплектация",
            "car_link": "https://che168.com/car/123456",
            "notes": "Тестовое предложение",
            "included_services": {
                "inspection": True,
                "export": True,
                "logistics_china": False,
                "delivery_rb": False,
                "insurance": False
            },
            "service_prices": {
                "inspection": "200",
                "export": "500"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/contractor-offers", json=offer_data, headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        
        assert response.status_code == 200, f"Create offer failed: {response.text}"
        data = response.json()
        assert "offer_id" in data
        assert data.get("message") == "Предложение отправлено"
        
        # Store offer_id for file upload tests
        return data["offer_id"]
    
    def test_create_offer_requires_tender_or_application(self, contractor_token):
        """Test that offer creation requires tender_id or application_id"""
        response = requests.post(f"{BASE_URL}/api/contractor-offers", json={
            "price_usd": 25000
        }, headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        
        assert response.status_code == 400
        assert "tender_id" in response.text.lower() or "application_id" in response.text.lower()


class TestOfferFileUpload:
    """Test offer file upload functionality"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Contractor login failed")
    
    @pytest.fixture(scope="class")
    def offer_id(self, contractor_token):
        """Create an offer and return its ID"""
        # First get an active tender
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard", headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        if response.status_code != 200:
            pytest.skip("Cannot get dashboard")
        
        tenders = response.json().get("tenders", [])
        if not tenders:
            pytest.skip("No active tenders")
        
        tender_id = tenders[0]["id"]
        
        # Create offer
        response = requests.post(f"{BASE_URL}/api/contractor-offers", json={
            "tender_id": tender_id,
            "price_usd": 20000,
            "car_brand": "Test",
            "car_model": "Model",
            "included_services": {"inspection": True},
            "service_prices": {"inspection": "100"}
        }, headers={
            "Authorization": f"Bearer {contractor_token}"
        })
        
        if response.status_code == 200:
            return response.json().get("offer_id")
        pytest.skip(f"Cannot create offer: {response.text}")
    
    def test_upload_photo_to_offer(self, contractor_token, offer_id):
        """Test uploading a photo file to an offer"""
        # Create a simple test image (1x1 pixel PNG)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            'file': ('test_photo.png', io.BytesIO(png_data), 'image/png')
        }
        data = {
            'file_type': 'photo'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor-offers/{offer_id}/files",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        assert "id" in result
        assert result.get("category") == "photo"
        assert result.get("original_name") == "test_photo.png"
        
        return result["id"]
    
    def test_get_offer_files(self, contractor_token, offer_id):
        """Test getting files for an offer"""
        response = requests.get(f"{BASE_URL}/api/offers/{offer_id}/files")
        
        assert response.status_code == 200, f"Get files failed: {response.text}"
        files = response.json()
        assert isinstance(files, list)
    
    def test_upload_to_nonexistent_offer(self, contractor_token):
        """Test uploading to non-existent offer returns 404"""
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            'file': ('test.png', io.BytesIO(png_data), 'image/png')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/contractor-offers/nonexistent-offer-id/files",
            files=files,
            data={'file_type': 'photo'},
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        
        assert response.status_code == 404


class TestOfferFileDownload:
    """Test offer file download functionality"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User login failed")
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor token"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Contractor login failed")
    
    def test_download_without_token_fails(self):
        """Test download without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/offer-files/some-file-id/download")
        assert response.status_code == 401
    
    def test_download_with_invalid_token_fails(self):
        """Test download with invalid token returns 401"""
        response = requests.get(f"{BASE_URL}/api/offer-files/some-file-id/download?token=invalid")
        assert response.status_code == 401
    
    def test_download_nonexistent_file(self, user_token):
        """Test download of non-existent file returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/offer-files/nonexistent-file-id/download?token={user_token}"
        )
        assert response.status_code == 404


class TestContractorPublicProfile:
    """Test contractor public profile endpoint"""
    
    @pytest.fixture(scope="class")
    def contractor_id(self):
        """Get a contractor ID"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": CONTRACTOR_EMAIL,
            "password": CONTRACTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("contractor", {}).get("id")
        pytest.skip("Cannot get contractor ID")
    
    def test_get_public_profile(self, contractor_id):
        """Test getting contractor public profile"""
        response = requests.get(f"{BASE_URL}/api/contractors/{contractor_id}/public-profile")
        
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "id" in data
        assert "company_name" in data
        assert "services" in data
        assert "rating" in data
        assert "verified" in data
        assert "completed_deals" in data
        assert "active_offers" in data
        assert "accepted_offers" in data
    
    def test_public_profile_no_password(self, contractor_id):
        """Test public profile does not expose password"""
        response = requests.get(f"{BASE_URL}/api/contractors/{contractor_id}/public-profile")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_nonexistent_contractor_profile(self):
        """Test getting profile of non-existent contractor returns 404"""
        response = requests.get(f"{BASE_URL}/api/contractors/nonexistent-id/public-profile")
        assert response.status_code == 404


class TestTendersEndpoint:
    """Test tenders endpoint returns offers with car details"""
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("User login failed")
    
    def test_tenders_endpoint_works(self, user_token):
        """Test tenders endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/tenders", headers={
            "Authorization": f"Bearer {user_token}"
        })
        
        assert response.status_code == 200, f"Tenders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
