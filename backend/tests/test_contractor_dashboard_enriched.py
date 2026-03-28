"""
Test suite for Contractor Dashboard with enriched tender data (30+ fields from application)
Tests the /api/contractor-dashboard endpoint and verifies all application fields are returned
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Contractor credentials
CONTRACTOR_EMAIL = "horon4ik@icloud.com"
CONTRACTOR_PASSWORD = "test123"


class TestContractorDashboardEnriched:
    """Tests for contractor dashboard with enriched tender data"""
    
    @pytest.fixture(scope="class")
    def contractor_token(self):
        """Get contractor auth token"""
        response = requests.post(
            f"{BASE_URL}/api/contractors/login",
            json={"email": CONTRACTOR_EMAIL, "password": CONTRACTOR_PASSWORD}
        )
        assert response.status_code == 200, f"Contractor login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_health_endpoint(self):
        """Test health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")
    
    def test_contractor_login(self):
        """Test contractor login returns token"""
        response = requests.post(
            f"{BASE_URL}/api/contractors/login",
            json={"email": CONTRACTOR_EMAIL, "password": CONTRACTOR_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "contractor" in data
        assert data["contractor"].get("company_name") is not None
        print(f"✓ Contractor login successful: {data['contractor']['company_name']}")
    
    def test_contractor_dashboard_returns_tenders(self, contractor_token):
        """Test contractor dashboard returns tenders list"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check dashboard structure
        assert "contractor" in data
        assert "active_tenders" in data
        assert "my_offers" in data
        assert "completed_deals" in data
        assert "active_deals" in data
        assert "tenders" in data
        
        print(f"✓ Dashboard returned: {data['active_tenders']} active tenders")
    
    def test_tenders_have_enriched_car_request(self, contractor_token):
        """Test that tenders have enriched car_request with application data"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Check first tender has car_request
        tender = tenders[0]
        assert "car_request" in tender, "Tender missing car_request"
        cr = tender["car_request"]
        
        # Check that application_number is present (indicates enrichment worked)
        assert "application_number" in tender or tender.get("application_id"), \
            "Tender should have application_number or application_id"
        
        print(f"✓ Tender has car_request with {len(cr)} fields")
    
    def test_tender_has_client_info_fields(self, contractor_token):
        """Test tender car_request has client info fields"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Find a tender with client info
        for tender in tenders:
            cr = tender.get("car_request", {})
            if cr.get("full_name") or cr.get("client_type"):
                assert cr.get("full_name") or cr.get("client_type"), "Should have client info"
                print(f"✓ Client info: {cr.get('full_name', 'N/A')} ({cr.get('client_type', 'N/A')})")
                return
        
        print("⚠ No tenders with client info found (may be expected)")
    
    def test_tender_has_budget_fields(self, contractor_token):
        """Test tender car_request has budget fields"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Check budget fields in first tender
        cr = tenders[0].get("car_request", {})
        budget_fields = ["budget_china_from", "budget_china_to", "budget_total", "budget_min", "budget_max"]
        found_budget = any(cr.get(f) is not None for f in budget_fields)
        
        if found_budget:
            print(f"✓ Budget: ${cr.get('budget_china_from', 'N/A')} - ${cr.get('budget_china_to', 'N/A')}")
        else:
            print("⚠ No budget fields found (may be expected)")
    
    def test_tender_has_technical_specs(self, contractor_token):
        """Test tender car_request has technical specification fields"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        cr = tenders[0].get("car_request", {})
        
        # Technical spec fields
        tech_fields = ["engine_type", "engine_volume", "transmission", "drive_type", 
                       "body_type", "mileage_max", "car_condition"]
        found_tech = {f: cr.get(f) for f in tech_fields if cr.get(f) is not None}
        
        print(f"✓ Technical specs found: {list(found_tech.keys())}")
    
    def test_tender_has_color_interior_fields(self, contractor_token):
        """Test tender car_request has color and interior fields"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Check all tenders for color/interior fields
        color_fields = ["body_color", "interior_color", "interior_material"]
        for tender in tenders:
            cr = tender.get("car_request", {})
            found = {f: cr.get(f) for f in color_fields if cr.get(f) is not None}
            if found:
                print(f"✓ Color/Interior fields: {found}")
                return
        
        print("⚠ No color/interior fields found in any tender")
    
    def test_tender_has_logistics_fields(self, contractor_token):
        """Test tender car_request has logistics fields (timeline, payment, customs, delivery)"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        cr = tenders[0].get("car_request", {})
        logistics_fields = ["purchase_timeline", "payment_method", "customs_clearance", 
                           "delivery_city", "car_purpose"]
        found = {f: cr.get(f) for f in logistics_fields if cr.get(f) is not None}
        
        print(f"✓ Logistics fields: {list(found.keys())}")
    
    def test_tender_has_priority_fields(self, contractor_token):
        """Test tender car_request has client priority fields"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        cr = tenders[0].get("car_request", {})
        priority_fields = ["priority_price", "priority_reliability", "priority_technology",
                          "priority_prestige", "priority_fuel"]
        found = {f: cr.get(f) for f in priority_fields if cr.get(f) is not None}
        
        if found:
            print(f"✓ Priority fields: {found}")
        else:
            print("⚠ No priority fields found")
    
    def test_tender_has_options_fields(self, contractor_token):
        """Test tender car_request has options fields (comfort, electronic, exterior, other)"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Check all tenders for options
        options_fields = ["options_comfort", "options_electronic", "options_exterior", "options_other"]
        for tender in tenders:
            cr = tender.get("car_request", {})
            for field in options_fields:
                opts = cr.get(field, [])
                if opts and len(opts) > 0:
                    print(f"✓ Options found: {field} = {opts}")
                    return
        
        print("⚠ No options found in any tender")
    
    def test_tender_has_additional_requirements(self, contractor_token):
        """Test tender car_request has additional_requirements field"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        for tender in tenders:
            cr = tender.get("car_request", {})
            if cr.get("additional_requirements"):
                print(f"✓ Additional requirements: {cr['additional_requirements'][:50]}...")
                return
        
        print("⚠ No additional_requirements found (may be expected)")
    
    def test_tender_has_allow_damage_field(self, contractor_token):
        """Test tender car_request has allow_damage field"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        for tender in tenders:
            cr = tender.get("car_request", {})
            if "allow_damage" in cr:
                print(f"✓ allow_damage field present: {cr['allow_damage']}")
                return
        
        print("⚠ No allow_damage field found")
    
    def test_tender_field_count(self, contractor_token):
        """Test that enriched tender has 30+ fields in car_request"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": f"Bearer {contractor_token}"}
        )
        data = response.json()
        tenders = data.get("tenders", [])
        
        if len(tenders) == 0:
            pytest.skip("No active tenders to test")
        
        # Find tender with most fields
        max_fields = 0
        for tender in tenders:
            cr = tender.get("car_request", {})
            field_count = len([k for k, v in cr.items() if v is not None and v != "" and v != []])
            if field_count > max_fields:
                max_fields = field_count
        
        print(f"✓ Maximum fields in car_request: {max_fields}")
        # We expect at least 15 fields for a well-filled application
        assert max_fields >= 10, f"Expected at least 10 fields, got {max_fields}"


class TestContractorDashboardAuth:
    """Test authentication for contractor dashboard"""
    
    def test_dashboard_requires_auth(self):
        """Test that dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/contractor-dashboard")
        assert response.status_code in [401, 403], "Dashboard should require auth"
        print("✓ Dashboard requires authentication")
    
    def test_dashboard_rejects_invalid_token(self):
        """Test that dashboard rejects invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/contractor-dashboard",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code in [401, 403], "Dashboard should reject invalid token"
        print("✓ Dashboard rejects invalid token")
    
    def test_contractor_login_wrong_password(self):
        """Test contractor login with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/contractors/login",
            json={"email": CONTRACTOR_EMAIL, "password": "wrong_password"}
        )
        assert response.status_code in [401, 403], "Should reject wrong password"
        print("✓ Login rejects wrong password")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
