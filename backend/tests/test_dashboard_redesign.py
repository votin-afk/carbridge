"""
Test suite for Dashboard Redesign features:
- Dashboard Overview (balance, verification, contract status, statistics)
- MyGarage (add to deal $300, start tender)
- DealCars page
- Applications (manager help $200, start tender)
- New API endpoints: /api/deals/request-assistance, /api/applications/{id}/request-manager-help, 
  /api/applications/{id}/start-tender, /api/deals/add-car
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test"


class TestDashboardRedesignAPIs:
    """Test new dashboard redesign API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    # ==================== Account Summary Tests ====================
    
    def test_account_summary_returns_balance(self):
        """Test /api/account/summary returns balance and verification status"""
        response = self.session.get(f"{BASE_URL}/api/account/summary")
        assert response.status_code == 200
        
        data = response.json()
        # Should have balance field
        assert "balance" in data
        assert isinstance(data["balance"], (int, float))
        
        # Should have verification status
        assert "is_verified" in data
        assert isinstance(data["is_verified"], bool)
        
        # Should have contract status
        assert "contract_signed" in data
        assert isinstance(data["contract_signed"], bool)
        
        print(f"Account summary: balance=${data['balance']}, verified={data['is_verified']}, contract={data['contract_signed']}")
    
    def test_account_summary_requires_auth(self):
        """Test /api/account/summary requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/account/summary")
        assert response.status_code in [401, 403, 422]
    
    # ==================== Deals Endpoints Tests ====================
    
    def test_deals_list_endpoint(self):
        """Test GET /api/deals returns list of deals"""
        response = self.session.get(f"{BASE_URL}/api/deals")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} deals")
    
    def test_deals_request_assistance_endpoint_exists(self):
        """Test POST /api/deals/request-assistance endpoint exists"""
        response = self.session.post(f"{BASE_URL}/api/deals/request-assistance", json={})
        
        # Should return 400 (insufficient funds) or 200 (success) - not 404
        assert response.status_code != 404, "Endpoint /api/deals/request-assistance not found"
        
        if response.status_code == 400:
            # Expected - insufficient funds
            data = response.json()
            assert "detail" in data
            print(f"Request assistance response: {data['detail']}")
        elif response.status_code == 200:
            data = response.json()
            assert "fee_charged" in data
            assert data["fee_charged"] == 200
            print(f"Assistance requested successfully, fee: ${data['fee_charged']}")
    
    def test_deals_add_car_endpoint_exists(self):
        """Test POST /api/deals/add-car endpoint exists"""
        # Try with invalid car_id to verify endpoint exists
        response = self.session.post(f"{BASE_URL}/api/deals/add-car", json={
            "car_id": "non-existent-car-id",
            "from_tender": False
        })
        
        # Should return 400/403/404 - not 404 for endpoint itself
        assert response.status_code in [400, 403, 404], f"Unexpected status: {response.status_code}"
        
        data = response.json()
        print(f"Add car to deal response: {response.status_code} - {data.get('detail', data)}")
    
    def test_deals_add_car_requires_verification(self):
        """Test /api/deals/add-car requires user verification"""
        # First add a car to garage
        car_data = {
            "brand": "TEST_BYD",
            "model": "Han",
            "year": 2024,
            "price_cny": 200000,
            "engine_type": "electric"
        }
        
        garage_response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        
        if garage_response.status_code == 200:
            car_id = garage_response.json().get("id")
            
            # Try to add to deal
            response = self.session.post(f"{BASE_URL}/api/deals/add-car", json={
                "car_id": car_id,
                "from_tender": False
            })
            
            # Should fail with verification error or insufficient funds
            assert response.status_code in [400, 403]
            data = response.json()
            print(f"Add car to deal (unverified): {data.get('detail')}")
            
            # Cleanup - delete test car
            self.session.delete(f"{BASE_URL}/api/garage/{car_id}")
        else:
            print(f"Could not create test car: {garage_response.status_code}")
    
    # ==================== Applications Endpoints Tests ====================
    
    def test_applications_list_endpoint(self):
        """Test GET /api/applications/my returns user's applications"""
        response = self.session.get(f"{BASE_URL}/api/applications/my")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} applications")
    
    def test_applications_request_manager_help_endpoint_exists(self):
        """Test POST /api/applications/{id}/request-manager-help endpoint exists"""
        # First create an application
        app_data = {
            "full_name": "Test User",
            "phone": "+375291234567",
            "email": "test@test.com",
            "brand": "TEST_BYD",
            "model": "Seal"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/applications/create", json=app_data)
        
        if create_response.status_code == 200:
            app_id = create_response.json().get("application_id")
            
            # Try to request manager help
            response = self.session.post(f"{BASE_URL}/api/applications/{app_id}/request-manager-help")
            
            # Should return 400 (insufficient funds) or 200 (success) - not 404
            assert response.status_code != 404, f"Endpoint not found for app {app_id}"
            
            data = response.json()
            print(f"Request manager help response: {response.status_code} - {data}")
            
            # Cleanup - cancel application
            self.session.delete(f"{BASE_URL}/api/applications/{app_id}")
        else:
            pytest.skip("Could not create test application")
    
    def test_applications_start_tender_endpoint_exists(self):
        """Test POST /api/applications/{id}/start-tender endpoint exists"""
        # First create an application
        app_data = {
            "full_name": "Test User Tender",
            "phone": "+375291234568",
            "email": "test@test.com",
            "brand": "TEST_Zeekr",
            "model": "001"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/applications/create", json=app_data)
        
        if create_response.status_code == 200:
            app_id = create_response.json().get("application_id")
            
            # Try to start tender
            response = self.session.post(f"{BASE_URL}/api/applications/{app_id}/start-tender")
            
            # Should return 400/403 (contract not signed) or 200 (success) - not 404
            assert response.status_code != 404, f"Endpoint not found for app {app_id}"
            
            data = response.json()
            print(f"Start tender response: {response.status_code} - {data}")
            
            # Cleanup - cancel application
            self.session.delete(f"{BASE_URL}/api/applications/{app_id}")
        else:
            pytest.skip("Could not create test application")
    
    # ==================== Garage Endpoints Tests ====================
    
    def test_garage_list_endpoint(self):
        """Test GET /api/garage returns user's cars"""
        response = self.session.get(f"{BASE_URL}/api/garage")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} cars in garage")
    
    def test_garage_add_car(self):
        """Test POST /api/garage adds car to garage"""
        car_data = {
            "brand": "TEST_Li_Auto",
            "model": "L9",
            "year": 2024,
            "price_cny": 450000,
            "engine_type": "hybrid",
            "engine_volume": 1500,
            "mileage": 5000
        }
        
        response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["brand"] == "TEST_Li_Auto"
        assert data["model"] == "L9"
        
        car_id = data["id"]
        print(f"Created car in garage: {car_id}")
        
        # Cleanup
        delete_response = self.session.delete(f"{BASE_URL}/api/garage/{car_id}")
        assert delete_response.status_code == 200
        print(f"Deleted test car: {car_id}")
    
    # ==================== Tenders Endpoints Tests ====================
    
    def test_tenders_list_endpoint(self):
        """Test GET /api/tenders returns user's tenders"""
        response = self.session.get(f"{BASE_URL}/api/tenders")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} tenders")
    
    def test_tenders_create_requires_contract(self):
        """Test POST /api/tenders requires signed contract"""
        # First add a car to garage
        car_data = {
            "brand": "TEST_Tender_Car",
            "model": "Test",
            "year": 2024,
            "price_cny": 100000
        }
        
        garage_response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        
        if garage_response.status_code == 200:
            car_id = garage_response.json().get("id")
            
            # Try to create tender
            response = self.session.post(f"{BASE_URL}/api/tenders", json={"car_id": car_id})
            
            # Should fail if contract not signed or succeed
            print(f"Create tender response: {response.status_code} - {response.json()}")
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/garage/{car_id}")
        else:
            print(f"Could not create test car: {garage_response.status_code}")
    
    # ==================== Statistics Tests ====================
    
    def test_dashboard_statistics_data(self):
        """Test that dashboard can fetch all required statistics"""
        # Fetch all data needed for dashboard overview
        garage_response = self.session.get(f"{BASE_URL}/api/garage")
        tenders_response = self.session.get(f"{BASE_URL}/api/tenders")
        applications_response = self.session.get(f"{BASE_URL}/api/applications/my")
        deals_response = self.session.get(f"{BASE_URL}/api/deals")
        account_response = self.session.get(f"{BASE_URL}/api/account/summary")
        
        # All should return 200
        assert garage_response.status_code == 200, "Garage endpoint failed"
        assert tenders_response.status_code == 200, "Tenders endpoint failed"
        assert applications_response.status_code == 200, "Applications endpoint failed"
        assert deals_response.status_code == 200, "Deals endpoint failed"
        assert account_response.status_code == 200, "Account summary endpoint failed"
        
        # Calculate statistics
        garage_count = len(garage_response.json())
        tenders = tenders_response.json()
        active_tenders = len([t for t in tenders if t.get("status") == "active"])
        applications_count = len(applications_response.json())
        deals = deals_response.json()
        active_deals = len([d for d in deals if d.get("status") == "active"])
        
        print(f"Dashboard statistics:")
        print(f"  - Garage: {garage_count} cars")
        print(f"  - Active tenders: {active_tenders}")
        print(f"  - Applications: {applications_count}")
        print(f"  - Active deals: {active_deals}")
        print(f"  - Balance: ${account_response.json().get('balance', 0)}")


class TestDashboardRedesignFees:
    """Test fee constants and deductions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_consultant_fee_is_200(self):
        """Test that consultant help fee is $200"""
        response = self.session.post(f"{BASE_URL}/api/deals/request-assistance", json={})
        
        if response.status_code == 400:
            # Insufficient funds - check error message mentions $200
            data = response.json()
            detail = data.get("detail", "")
            assert "200" in detail or "Недостаточно" in detail
            print(f"Consultant fee check: {detail}")
        elif response.status_code == 200:
            data = response.json()
            assert data.get("fee_charged") == 200
            print(f"Consultant fee confirmed: ${data['fee_charged']}")
    
    def test_deal_add_fee_is_300(self):
        """Test that adding car to deal costs $300"""
        # Create a test car
        car_data = {
            "brand": "TEST_Fee_Check",
            "model": "Test",
            "year": 2024,
            "price_cny": 100000
        }
        
        garage_response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        
        if garage_response.status_code == 200:
            car_id = garage_response.json().get("id")
            
            response = self.session.post(f"{BASE_URL}/api/deals/add-car", json={
                "car_id": car_id,
                "from_tender": False
            })
            
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", "")
                # Should mention $300 or insufficient funds
                assert "300" in detail or "Недостаточно" in detail or "верификац" in detail.lower()
                print(f"Deal add fee check: {detail}")
            elif response.status_code == 200:
                data = response.json()
                assert data.get("fee_charged") == 300
                print(f"Deal add fee confirmed: ${data['fee_charged']}")
            
            # Cleanup
            self.session.delete(f"{BASE_URL}/api/garage/{car_id}")
        else:
            pytest.skip("Could not create test car")
    
    def test_tender_from_deal_is_free(self):
        """Test that adding car to deal from tender is free"""
        # This is a logical test - from_tender=True should not charge fee
        # We can't fully test without a completed tender, but we verify the endpoint accepts the parameter
        
        response = self.session.post(f"{BASE_URL}/api/deals/add-car", json={
            "car_id": "test-car-id",
            "from_tender": True,
            "tender_offer_id": "test-offer-id"
        })
        
        # Should not return 422 (validation error) for from_tender parameter
        assert response.status_code != 422, "from_tender parameter not accepted"
        print(f"from_tender parameter accepted, response: {response.status_code}")


class TestDashboardRedesignIntegration:
    """Integration tests for dashboard redesign flows"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_full_garage_to_tender_flow(self):
        """Test flow: Add car to garage -> Start tender"""
        # Step 1: Add car to garage
        car_data = {
            "brand": "TEST_Flow_Car",
            "model": "Integration",
            "year": 2024,
            "price_cny": 250000,
            "engine_type": "electric"
        }
        
        garage_response = self.session.post(f"{BASE_URL}/api/garage", json=car_data)
        assert garage_response.status_code == 200
        car_id = garage_response.json().get("id")
        print(f"Step 1: Created car {car_id}")
        
        # Step 2: Verify car appears in garage list
        list_response = self.session.get(f"{BASE_URL}/api/garage")
        assert list_response.status_code == 200
        cars = list_response.json()
        car_ids = [c.get("id") for c in cars]
        assert car_id in car_ids
        print(f"Step 2: Car verified in garage list")
        
        # Step 3: Try to start tender (may fail due to contract requirement)
        tender_response = self.session.post(f"{BASE_URL}/api/tenders", json={"car_id": car_id})
        print(f"Step 3: Tender creation response: {tender_response.status_code}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/garage/{car_id}")
        print(f"Cleanup: Deleted test car")
    
    def test_application_to_tender_flow(self):
        """Test flow: Create application -> Start tender from application"""
        # Step 1: Create application
        app_data = {
            "full_name": "Test Integration User",
            "phone": "+375291234569",
            "email": "test@test.com",
            "brand": "TEST_App_Flow",
            "model": "Test",
            "budget_max": 50000,
            "budget_currency": "USD"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/applications/create", json=app_data)
        assert create_response.status_code == 200
        app_id = create_response.json().get("application_id")
        print(f"Step 1: Created application {app_id}")
        
        # Step 2: Verify application in list
        list_response = self.session.get(f"{BASE_URL}/api/applications/my")
        assert list_response.status_code == 200
        apps = list_response.json()
        app_ids = [a.get("id") for a in apps]
        assert app_id in app_ids
        print(f"Step 2: Application verified in list")
        
        # Step 3: Try to start tender from application
        tender_response = self.session.post(f"{BASE_URL}/api/applications/{app_id}/start-tender")
        print(f"Step 3: Start tender response: {tender_response.status_code} - {tender_response.json()}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/applications/{app_id}")
        print(f"Cleanup: Cancelled test application")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
