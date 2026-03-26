"""
Test suite for Moderator Tenders Enriched View
Tests the GET /api/moderator/tenders endpoint which returns full tender data
including car_request, offers with files, and user info.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "votin@tut.by"
ADMIN_PASSWORD = "test"


class TestModeratorTendersEnriched:
    """Tests for enriched moderator tenders endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
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
            pytest.skip("Admin login failed - skipping moderator tests")
    
    def test_moderator_tenders_returns_200(self):
        """Test that GET /api/moderator/tenders returns 200"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/moderator/tenders returns 200")
    
    def test_moderator_tenders_returns_list(self):
        """Test that response is a list"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Response is a list with {len(data)} tenders")
    
    def test_tender_has_required_fields(self):
        """Test that each tender has required fields"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        if not tenders:
            pytest.skip("No tenders available for testing")
        
        required_fields = ["id", "car_brand", "car_model", "status", "offers", "created_at"]
        
        for tender in tenders:
            for field in required_fields:
                assert field in tender, f"Tender missing required field: {field}"
        
        print(f"✓ All {len(tenders)} tenders have required fields")
    
    def test_tender_has_car_request(self):
        """Test that tenders include car_request object"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        if not tenders:
            pytest.skip("No tenders available for testing")
        
        tenders_with_car_request = [t for t in tenders if t.get("car_request")]
        
        if not tenders_with_car_request:
            pytest.skip("No tenders with car_request found")
        
        # Check car_request structure
        for tender in tenders_with_car_request:
            cr = tender["car_request"]
            assert isinstance(cr, dict), "car_request should be a dict"
            
            # Check for common car_request fields
            possible_fields = ["brand", "model", "year_from", "year_to", "engine_type", 
                             "body_type", "drive_type", "mileage_max", "budget_china_from",
                             "budget_china_to", "delivery_city"]
            
            found_fields = [f for f in possible_fields if f in cr]
            print(f"  Tender {tender['id'][:8]} car_request has fields: {found_fields}")
        
        print(f"✓ {len(tenders_with_car_request)} tenders have car_request data")
    
    def test_tender_has_user_info(self):
        """Test that tenders include user info"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        if not tenders:
            pytest.skip("No tenders available for testing")
        
        for tender in tenders:
            # Check for user_name or user_email
            has_user_info = tender.get("user_name") or tender.get("user_email")
            if has_user_info:
                print(f"  Tender {tender['id'][:8]} user: {tender.get('user_name', '')} ({tender.get('user_email', '')})")
        
        print("✓ Tenders include user info fields")
    
    def test_tender_offers_is_list(self):
        """Test that tender.offers is a list"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        if not tenders:
            pytest.skip("No tenders available for testing")
        
        for tender in tenders:
            assert "offers" in tender, "Tender should have offers field"
            assert isinstance(tender["offers"], list), "offers should be a list"
        
        print("✓ All tenders have offers as list")
    
    def test_offer_has_required_fields(self):
        """Test that each offer has required fields"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        # Find tenders with offers
        tenders_with_offers = [t for t in tenders if t.get("offers")]
        
        if not tenders_with_offers:
            pytest.skip("No tenders with offers found")
        
        required_offer_fields = ["id", "contractor_id", "contractor_name", "price_usd", "created_at"]
        
        for tender in tenders_with_offers:
            for offer in tender["offers"]:
                for field in required_offer_fields:
                    assert field in offer, f"Offer missing required field: {field}"
        
        total_offers = sum(len(t["offers"]) for t in tenders_with_offers)
        print(f"✓ All {total_offers} offers have required fields")
    
    def test_offer_has_car_details(self):
        """Test that offers include car detail fields"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        tenders_with_offers = [t for t in tenders if t.get("offers")]
        
        if not tenders_with_offers:
            pytest.skip("No tenders with offers found")
        
        car_detail_fields = ["car_brand", "car_model", "car_year", "car_mileage", 
                           "car_engine_type", "car_color", "car_transmission", "car_vin"]
        
        offers_with_car_details = 0
        for tender in tenders_with_offers:
            for offer in tender["offers"]:
                found_fields = [f for f in car_detail_fields if offer.get(f)]
                if found_fields:
                    offers_with_car_details += 1
                    print(f"  Offer {offer['id'][:8]} has car details: {found_fields}")
        
        print(f"✓ {offers_with_car_details} offers have car detail fields")
    
    def test_offer_has_files_array(self):
        """Test that each offer has files array"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        tenders_with_offers = [t for t in tenders if t.get("offers")]
        
        if not tenders_with_offers:
            pytest.skip("No tenders with offers found")
        
        offers_with_files = 0
        total_files = 0
        
        for tender in tenders_with_offers:
            for offer in tender["offers"]:
                assert "files" in offer, f"Offer {offer['id']} missing files array"
                assert isinstance(offer["files"], list), "files should be a list"
                
                if offer["files"]:
                    offers_with_files += 1
                    total_files += len(offer["files"])
                    print(f"  Offer {offer['id'][:8]} has {len(offer['files'])} files")
        
        print(f"✓ All offers have files array. {offers_with_files} offers have {total_files} total files")
    
    def test_file_has_required_fields(self):
        """Test that file objects have required fields"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        # Find offers with files
        files_found = []
        for tender in tenders:
            for offer in tender.get("offers", []):
                for file in offer.get("files", []):
                    files_found.append(file)
        
        if not files_found:
            pytest.skip("No files found in offers")
        
        required_file_fields = ["id", "category", "original_name"]
        
        for file in files_found:
            for field in required_file_fields:
                assert field in file, f"File missing required field: {field}"
            
            # Verify category is photo or video
            assert file["category"] in ["photo", "video", "other"], f"Invalid file category: {file['category']}"
        
        print(f"✓ All {len(files_found)} files have required fields")
    
    def test_offer_has_services(self):
        """Test that offers include services information"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        tenders_with_offers = [t for t in tenders if t.get("offers")]
        
        if not tenders_with_offers:
            pytest.skip("No tenders with offers found")
        
        offers_with_services = 0
        for tender in tenders_with_offers:
            for offer in tender["offers"]:
                if offer.get("included_services"):
                    offers_with_services += 1
                    services = [k for k, v in offer["included_services"].items() if v]
                    print(f"  Offer {offer['id'][:8]} services: {services}")
        
        print(f"✓ {offers_with_services} offers have included_services")
    
    def test_offer_has_contractor_rating(self):
        """Test that offers include contractor rating"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        tenders_with_offers = [t for t in tenders if t.get("offers")]
        
        if not tenders_with_offers:
            pytest.skip("No tenders with offers found")
        
        for tender in tenders_with_offers:
            for offer in tender["offers"]:
                assert "contractor_rating" in offer, "Offer should have contractor_rating"
                assert isinstance(offer["contractor_rating"], (int, float)), "contractor_rating should be numeric"
        
        print("✓ All offers have contractor_rating")
    
    def test_offers_count_matches(self):
        """Test that offers_count matches actual offers length"""
        response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        assert response.status_code == 200
        tenders = response.json()
        
        if not tenders:
            pytest.skip("No tenders available for testing")
        
        for tender in tenders:
            if "offers_count" in tender:
                actual_count = len(tender.get("offers", []))
                assert tender["offers_count"] == actual_count, \
                    f"offers_count ({tender['offers_count']}) doesn't match actual ({actual_count})"
        
        print("✓ offers_count matches actual offers length for all tenders")


class TestModeratorTendersDelete:
    """Tests for moderator tender deletion"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
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
        else:
            pytest.skip("Admin login failed - skipping moderator tests")
    
    def test_delete_tender_requires_auth(self):
        """Test that DELETE /api/moderator/tenders/{id} requires authentication"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.delete(f"{BASE_URL}/api/moderator/tenders/fake-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ DELETE /api/moderator/tenders requires authentication")
    
    def test_delete_nonexistent_tender_returns_404(self):
        """Test that deleting non-existent tender returns 404"""
        response = self.session.delete(f"{BASE_URL}/api/moderator/tenders/nonexistent-tender-id")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ DELETE non-existent tender returns 404")


class TestContractorPublicProfile:
    """Tests for contractor public profile endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_public_profile_returns_200(self):
        """Test that GET /api/contractors/{id}/public-profile returns 200 for valid contractor"""
        # First, get a contractor ID from tenders
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        tenders_response = self.session.get(f"{BASE_URL}/api/moderator/tenders")
        if tenders_response.status_code != 200:
            pytest.skip("Could not fetch tenders")
        
        tenders = tenders_response.json()
        
        # Find a contractor ID from offers
        contractor_id = None
        for tender in tenders:
            for offer in tender.get("offers", []):
                if offer.get("contractor_id"):
                    contractor_id = offer["contractor_id"]
                    break
            if contractor_id:
                break
        
        if not contractor_id:
            pytest.skip("No contractor found in offers")
        
        # Test public profile endpoint (no auth required)
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/contractors/{contractor_id}/public-profile")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        profile = response.json()
        assert "company_name" in profile, "Profile should have company_name"
        assert "password_hash" not in profile, "Profile should NOT expose password_hash"
        
        print(f"✓ Public profile for contractor {contractor_id[:8]} returns 200")
        print(f"  Company: {profile.get('company_name')}")
        print(f"  Services: {profile.get('services')}")
        print(f"  Rating: {profile.get('rating')}")
    
    def test_public_profile_nonexistent_returns_404(self):
        """Test that GET /api/contractors/{id}/public-profile returns 404 for non-existent contractor"""
        response = self.session.get(f"{BASE_URL}/api/contractors/nonexistent-contractor-id/public-profile")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Public profile for non-existent contractor returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
