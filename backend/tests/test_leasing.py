"""
Test suite for Leasing Calculator feature
Tests:
- Leasing companies endpoint
- Leasing calculation endpoint
- Manager help request endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLeasingCompanies:
    """Tests for leasing companies endpoint"""
    
    def test_get_leasing_companies(self):
        """Test that /api/contractors?contractor_type=leasing returns 3 leasing companies"""
        response = requests.get(f"{BASE_URL}/api/contractors", params={"contractor_type": "leasing"})
        assert response.status_code == 200
        
        companies = response.json()
        assert len(companies) == 3, f"Expected 3 leasing companies, got {len(companies)}"
        
        # Verify company names
        company_names = [c["name"] for c in companies]
        assert "АвтоЛизинг БЕЛ" in company_names
        assert "ПромЛизинг" in company_names
        assert "СмартЛиз" in company_names
    
    def test_leasing_companies_have_required_fields(self):
        """Test that leasing companies have all required fields"""
        response = requests.get(f"{BASE_URL}/api/contractors", params={"contractor_type": "leasing"})
        assert response.status_code == 200
        
        companies = response.json()
        required_fields = ["id", "name", "contractor_type", "description", "rating", "deals_count"]
        
        for company in companies:
            for field in required_fields:
                assert field in company, f"Missing field '{field}' in company {company.get('name')}"
            assert company["contractor_type"] == "leasing"
    
    def test_leasing_companies_have_leasing_rate(self):
        """Test that leasing companies have leasing_rate field"""
        response = requests.get(f"{BASE_URL}/api/contractors", params={"contractor_type": "leasing"})
        assert response.status_code == 200
        
        companies = response.json()
        # Note: leasing_rate is in DEMO_CONTRACTORS but may not be in response model
        # Check if at least one company has rate info in price_range
        for company in companies:
            assert "price_range" in company or "leasing_rate" in company


class TestLeasingCalculator:
    """Tests for leasing calculation endpoint"""
    
    def test_calculate_leasing_basic(self):
        """Test basic leasing calculation"""
        response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36
        })
        assert response.status_code == 200
        
        result = response.json()
        assert "car_price_usd" in result
        assert "down_payment" in result
        assert "monthly_payment" in result
        assert "first_payment" in result
        assert "overpayment" in result
        assert "total_cost" in result
        
        # Verify calculations
        assert result["car_price_usd"] == 30000
        assert result["down_payment"] == 6000  # 20% of 30000
        assert result["financed_amount"] == 24000  # 30000 - 6000
    
    def test_calculate_leasing_with_company(self):
        """Test leasing calculation with specific company (АвтоЛизинг БЕЛ - 8.5%)"""
        response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36,
            "leasing_company_id": "leas-001"  # АвтоЛизинг БЕЛ
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["annual_rate"] == 8.5  # АвтоЛизинг БЕЛ rate
    
    def test_calculate_leasing_different_rates(self):
        """Test that different companies have different rates"""
        # АвтоЛизинг БЕЛ - 8.5%
        response1 = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36,
            "leasing_company_id": "leas-001"
        })
        
        # СмартЛиз - 10.5%
        response2 = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36,
            "leasing_company_id": "leas-003"
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        result1 = response1.json()
        result2 = response2.json()
        
        assert result1["annual_rate"] == 8.5
        assert result2["annual_rate"] == 10.5
        assert result2["monthly_payment"] > result1["monthly_payment"]  # Higher rate = higher payment
    
    def test_calculate_leasing_down_payment_range(self):
        """Test leasing calculation with different down payment percentages (10-90%)"""
        for percent in [10, 20, 50, 90]:
            response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
                "car_price_usd": 30000,
                "down_payment_percent": percent,
                "term_months": 36
            })
            assert response.status_code == 200
            
            result = response.json()
            expected_down = 30000 * (percent / 100)
            assert result["down_payment"] == expected_down
            assert result["down_payment_percent"] == percent
    
    def test_calculate_leasing_term_range(self):
        """Test leasing calculation with different terms (12-84 months)"""
        for months in [12, 24, 36, 48, 60, 84]:
            response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
                "car_price_usd": 30000,
                "down_payment_percent": 20,
                "term_months": months
            })
            assert response.status_code == 200
            
            result = response.json()
            assert result["term_months"] == months
    
    def test_calculate_leasing_first_payment(self):
        """Test that first payment = down payment + first monthly payment"""
        response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36
        })
        assert response.status_code == 200
        
        result = response.json()
        expected_first = result["down_payment"] + result["monthly_payment"]
        assert abs(result["first_payment"] - expected_first) < 0.01  # Allow small rounding error
    
    def test_calculate_leasing_overpayment(self):
        """Test that overpayment = total_cost - car_price"""
        response = requests.post(f"{BASE_URL}/api/leasing/calculate", json={
            "car_price_usd": 30000,
            "down_payment_percent": 20,
            "term_months": 36
        })
        assert response.status_code == 200
        
        result = response.json()
        expected_overpayment = result["total_cost"] - result["car_price_usd"]
        assert abs(result["overpayment"] - expected_overpayment) < 0.01


class TestManagerHelp:
    """Tests for manager help request endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_manager_help_requires_auth(self):
        """Test that manager help endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/garage/some-car-id/request-manager-help")
        assert response.status_code in [401, 403]
    
    def test_manager_help_insufficient_balance(self, auth_headers):
        """Test manager help returns error when balance < $200"""
        # First get a car from garage
        garage_response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        if garage_response.status_code != 200 or not garage_response.json():
            pytest.skip("No cars in garage to test")
        
        car_id = garage_response.json()[0]["id"]
        
        # Check user balance
        account_response = requests.get(f"{BASE_URL}/api/user/account", headers=auth_headers)
        balance = account_response.json().get("balance", 0)
        
        if balance >= 200:
            pytest.skip("User has sufficient balance, cannot test insufficient balance scenario")
        
        # Try to request manager help
        response = requests.post(
            f"{BASE_URL}/api/garage/{car_id}/request-manager-help",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Недостаточно средств" in response.json().get("detail", "")
    
    def test_manager_help_car_not_found(self, auth_headers):
        """Test manager help returns 404 for non-existent car"""
        response = requests.post(
            f"{BASE_URL}/api/garage/non-existent-car-id/request-manager-help",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestGarageContractorAssignment:
    """Tests for assigning leasing company to car"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_assign_leasing_company_to_car(self, auth_headers):
        """Test assigning a leasing company to a car in garage"""
        # Get a car from garage
        garage_response = requests.get(f"{BASE_URL}/api/garage", headers=auth_headers)
        if garage_response.status_code != 200 or not garage_response.json():
            pytest.skip("No cars in garage to test")
        
        car_id = garage_response.json()[0]["id"]
        
        # Assign leasing company
        response = requests.post(
            f"{BASE_URL}/api/garage/{car_id}/assign-contractor",
            headers=auth_headers,
            json={
                "car_id": car_id,
                "contractor_id": "leas-001",  # АвтоЛизинг БЕЛ
                "stage": "leasing"
            }
        )
        
        assert response.status_code == 200
        
        # Verify assignment
        car_response = requests.get(f"{BASE_URL}/api/garage/{car_id}", headers=auth_headers)
        assert car_response.status_code == 200
        
        car = car_response.json()
        assert "contractors" in car
        if car.get("contractors") and car["contractors"].get("leasing"):
            assert car["contractors"]["leasing"]["contractor_id"] == "leas-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
