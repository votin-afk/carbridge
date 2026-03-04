"""
Test suite for new CARBRIDGE features:
1. Client Verification System
2. Car Application Form
3. Contractor Registration and Dashboard
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sino-auto-trade.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test@test.com"
TEST_USER_PASSWORD = "test"

class TestClientVerification:
    """Tests for Client Verification System"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_verification_status_initial(self):
        """Test getting verification status when not started"""
        response = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"Verification status: {data['status']}")
    
    def test_submit_verification_data(self):
        """Test submitting verification data"""
        verification_data = {
            "full_name": "Тестов Тест Тестович",
            "passport_series": "AB",
            "passport_number": "1234567",
            "passport_issued_by": "Минским ГОВД",
            "passport_issue_date": "2020-01-15",
            "registration_address": "г. Минск, ул. Тестовая, д. 1, кв. 1",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "client_type": "individual"
        }
        
        response = requests.post(f"{BASE_URL}/api/verification/submit", 
                                json=verification_data, headers=self.headers)
        assert response.status_code == 200, f"Submit failed: {response.text}"
        data = response.json()
        assert "verification_id" in data
        assert "contract_number" in data
        assert data["contract_number"].startswith("CB-")
        print(f"Verification submitted: {data['contract_number']}")
    
    def test_get_verification_status_after_submit(self):
        """Test getting verification status after submission"""
        response = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["pending", "documents_uploaded", "under_review", "approved", "rejected", "not_started"]
        if data["verification"]:
            assert "contract_number" in data["verification"]
            print(f"Verification status: {data['status']}, Contract: {data['verification']['contract_number']}")
    
    def test_upload_verification_document(self):
        """Test uploading document for verification"""
        # First ensure verification exists
        status_response = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        if status_response.json().get("status") == "not_started":
            # Submit verification first
            verification_data = {
                "full_name": "Тестов Тест Тестович",
                "passport_series": "AB",
                "passport_number": "1234567",
                "passport_issued_by": "Минским ГОВД",
                "passport_issue_date": "2020-01-15",
                "registration_address": "г. Минск, ул. Тестовая, д. 1, кв. 1",
                "phone": "+375291234567",
                "email": TEST_USER_EMAIL,
                "client_type": "individual"
            }
            requests.post(f"{BASE_URL}/api/verification/submit", 
                         json=verification_data, headers=self.headers)
        
        doc_data = {
            "doc_type": "passport_scan",
            "file_url": "https://example.com/passport_scan.jpg",
            "file_name": "passport_scan.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/api/verification/upload-document",
                                json=doc_data, headers=self.headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "document_id" in data
        print(f"Document uploaded: {data['document_id']}")
    
    def test_upload_document_missing_fields(self):
        """Test upload document with missing fields"""
        response = requests.post(f"{BASE_URL}/api/verification/upload-document",
                                json={"doc_type": "passport_scan"}, headers=self.headers)
        assert response.status_code == 400
    
    def test_get_contract(self):
        """Test getting contract data"""
        response = requests.get(f"{BASE_URL}/api/verification/contract", headers=self.headers)
        # May return 404 if no verification exists
        if response.status_code == 200:
            data = response.json()
            assert "contract_number" in data
            assert "executor" in data
            assert "client" in data
            assert "terms" in data
            print(f"Contract retrieved: {data['contract_number']}")
        else:
            assert response.status_code == 404
            print("No verification found for contract")
    
    def test_sign_contract(self):
        """Test signing contract"""
        # First check if documents are uploaded
        status_response = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        status = status_response.json().get("status")
        
        if status in ["documents_uploaded", "under_review", "approved"]:
            response = requests.post(f"{BASE_URL}/api/verification/sign-contract", 
                                    json={}, headers=self.headers)
            assert response.status_code == 200, f"Sign failed: {response.text}"
            data = response.json()
            assert "message" in data
            print(f"Contract signed: {data['message']}")
        else:
            print(f"Cannot sign contract - status is: {status}")


class TestCarApplications:
    """Tests for Car Application Form"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_application_minimal(self):
        """Test creating application with minimal data"""
        app_data = {
            "full_name": "Тестов Тест Тестович",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "client_type": "individual",
            "preferred_contact": "phone"
        }
        
        response = requests.post(f"{BASE_URL}/api/applications/create",
                                json=app_data, headers=self.headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "application_id" in data
        assert "application_number" in data
        assert data["application_number"].startswith("APP-")
        print(f"Application created: {data['application_number']}")
        return data["application_id"]
    
    def test_create_application_full(self):
        """Test creating application with full data"""
        app_data = {
            "client_type": "individual",
            "full_name": "Иванов Иван Иванович",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "preferred_contact": "telegram",
            "brand": "BYD",
            "model": "Han EV",
            "body_type": "sedan",
            "engine_type": "electric",
            "year_from": 2022,
            "year_to": 2024,
            "mileage_max": 50000,
            "budget_min": 30000,
            "budget_max": 50000,
            "budget_currency": "USD",
            "color_preferences": "Белый, чёрный",
            "transmission": "auto",
            "drive_type": "awd",
            "has_decree_140": False,
            "payment_method": "full",
            "needs_manager_help": True,
            "additional_requirements": "Желательно с панорамной крышей",
            "urgent": False
        }
        
        response = requests.post(f"{BASE_URL}/api/applications/create",
                                json=app_data, headers=self.headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "application_id" in data
        print(f"Full application created: {data['application_number']}")
        return data["application_id"]
    
    def test_create_application_with_decree_140(self):
        """Test creating application with Decree 140 benefits"""
        app_data = {
            "full_name": "Многодетный Тест",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "client_type": "individual",
            "preferred_contact": "phone",
            "has_decree_140": True,
            "decree_140_category": "many_children",
            "payment_method": "full"
        }
        
        response = requests.post(f"{BASE_URL}/api/applications/create",
                                json=app_data, headers=self.headers)
        assert response.status_code == 200
        print("Application with Decree 140 created")
    
    def test_get_my_applications(self):
        """Test getting user's applications list"""
        response = requests.get(f"{BASE_URL}/api/applications/my", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} applications")
        if data:
            app = data[0]
            assert "id" in app
            assert "application_number" in app
            assert "status" in app
    
    def test_get_specific_application(self):
        """Test getting specific application"""
        # First create an application
        app_data = {
            "full_name": "Тест Получения",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "client_type": "individual",
            "preferred_contact": "phone"
        }
        create_response = requests.post(f"{BASE_URL}/api/applications/create",
                                       json=app_data, headers=self.headers)
        app_id = create_response.json()["application_id"]
        
        # Get the application
        response = requests.get(f"{BASE_URL}/api/applications/{app_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == app_id
        assert data["full_name"] == "Тест Получения"
        print(f"Retrieved application: {data['application_number']}")
    
    def test_get_nonexistent_application(self):
        """Test getting non-existent application"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/applications/{fake_id}", headers=self.headers)
        assert response.status_code == 404
    
    def test_cancel_application(self):
        """Test cancelling application"""
        # First create an application
        app_data = {
            "full_name": "Тест Отмены",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "client_type": "individual",
            "preferred_contact": "phone"
        }
        create_response = requests.post(f"{BASE_URL}/api/applications/create",
                                       json=app_data, headers=self.headers)
        app_id = create_response.json()["application_id"]
        
        # Cancel the application
        response = requests.delete(f"{BASE_URL}/api/applications/{app_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"Application cancelled: {data['message']}")
    
    def test_cancel_nonexistent_application(self):
        """Test cancelling non-existent application"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/applications/{fake_id}", headers=self.headers)
        assert response.status_code == 400


class TestContractorRegistration:
    """Tests for Contractor Registration System"""
    
    def test_register_contractor_china(self):
        """Test registering contractor from China"""
        unique_email = f"test_contractor_cn_{uuid.uuid4().hex[:8]}@test.com"
        
        contractor_data = {
            "company_name": "测试公司 Test Company",
            "country": "CN",
            "registration_number": "91310000MA1FL5XX0L",
            "legal_address": "上海市浦东新区XX路XX号",
            "contact_person": "张三",
            "position": "经理",
            "phone": "+8613812345678",
            "email": unique_email,
            "whatsapp": "+8613812345678",
            "wechat": "test_wechat",
            "telegram": "@test_telegram",
            "services": ["inspection", "purchase", "export"],
            "description": "专业汽车出口公司，10年经验",
            "experience_years": 10,
            "website": "https://test-company.cn"
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        assert "contractor_id" in data
        assert "message" in data
        print(f"Contractor registered: {data['contractor_id']}")
    
    def test_register_contractor_belarus(self):
        """Test registering contractor from Belarus"""
        unique_email = f"test_contractor_by_{uuid.uuid4().hex[:8]}@test.com"
        
        contractor_data = {
            "company_name": "ООО Тест Логистика",
            "country": "BY",
            "registration_number": "123456789",
            "legal_address": "г. Минск, ул. Тестовая, д. 1",
            "contact_person": "Иванов Иван",
            "position": "Директор",
            "phone": "+375291234567",
            "email": unique_email,
            "telegram": "@test_by",
            "services": ["logistics", "customs"],
            "description": "Логистическая компания, растаможка авто из Китая",
            "experience_years": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        assert "contractor_id" in data
        print(f"Belarus contractor registered: {data['contractor_id']}")
    
    def test_register_contractor_all_services(self):
        """Test registering contractor with all services"""
        unique_email = f"test_contractor_all_{uuid.uuid4().hex[:8]}@test.com"
        
        contractor_data = {
            "company_name": "Full Service Company",
            "country": "CN",
            "legal_address": "Shanghai, China",
            "contact_person": "Test Person",
            "position": "Manager",
            "phone": "+8613812345678",
            "email": unique_email,
            "services": ["inspection", "purchase", "export", "logistics", "leasing", "customs"],
            "description": "Full service auto import company"
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response.status_code == 200
        print("Contractor with all services registered")
    
    def test_register_contractor_duplicate_email(self):
        """Test registering contractor with duplicate email"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@test.com"
        
        contractor_data = {
            "company_name": "First Company",
            "country": "CN",
            "legal_address": "Shanghai",
            "contact_person": "Test",
            "position": "Manager",
            "phone": "+8613812345678",
            "email": unique_email,
            "services": ["inspection"],
            "description": "Test company"
        }
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response1.status_code == 200
        
        # Second registration with same email
        contractor_data["company_name"] = "Second Company"
        response2 = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response2.status_code == 400
        print("Duplicate email correctly rejected")
    
    def test_register_contractor_missing_required_fields(self):
        """Test registering contractor with missing required fields"""
        contractor_data = {
            "company_name": "Incomplete Company"
            # Missing required fields
        }
        
        response = requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        assert response.status_code == 422  # Validation error
        print("Missing fields correctly rejected")


class TestContractorLogin:
    """Tests for Contractor Login"""
    
    def test_contractor_login_invalid_credentials(self):
        """Test contractor login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_contractor_login_unapproved(self):
        """Test contractor login when not approved"""
        # Register a new contractor
        unique_email = f"test_unapproved_{uuid.uuid4().hex[:8]}@test.com"
        
        contractor_data = {
            "company_name": "Unapproved Company",
            "country": "CN",
            "legal_address": "Shanghai",
            "contact_person": "Test",
            "position": "Manager",
            "phone": "+8613812345678",
            "email": unique_email,
            "services": ["inspection"],
            "description": "Test company"
        }
        
        requests.post(f"{BASE_URL}/api/contractors/register", json=contractor_data)
        
        # Try to login (should fail - not approved)
        response = requests.post(f"{BASE_URL}/api/contractors/login", json={
            "email": unique_email,
            "password": "anypassword"
        })
        # Should fail because contractor is not approved yet
        assert response.status_code in [401, 403]
        print("Unapproved contractor login correctly rejected")


class TestContractorDashboard:
    """Tests for Contractor Dashboard"""
    
    def test_dashboard_without_auth(self):
        """Test accessing dashboard without authentication"""
        response = requests.get(f"{BASE_URL}/api/contractors/dashboard")
        assert response.status_code in [401, 403]
        print("Unauthenticated dashboard access rejected")
    
    def test_dashboard_with_invalid_token(self):
        """Test accessing dashboard with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BASE_URL}/api/contractors/dashboard", headers=headers)
        assert response.status_code == 401
        print("Invalid token correctly rejected")


class TestModeratorContractorManagement:
    """Tests for Moderator Contractor Management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_contractor_applications(self):
        """Test getting contractor applications list"""
        response = requests.get(f"{BASE_URL}/api/moderator/contractor-applications", 
                               headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} contractor applications")
    
    def test_approve_nonexistent_contractor(self):
        """Test approving non-existent contractor"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/moderator/contractors/{fake_id}/approve",
                                json={"password": "test123"}, headers=self.headers)
        assert response.status_code == 404
        print("Non-existent contractor approval correctly rejected")
    
    def test_reject_nonexistent_contractor(self):
        """Test rejecting non-existent contractor"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/moderator/contractors/{fake_id}/reject",
                                json={"reason": "Test rejection"}, headers=self.headers)
        assert response.status_code == 404
        print("Non-existent contractor rejection correctly rejected")


class TestContractorOffers:
    """Tests for Contractor Offer Submission"""
    
    def test_submit_offer_without_auth(self):
        """Test submitting offer without authentication"""
        offer_data = {
            "tender_id": str(uuid.uuid4()),
            "price_usd": 35000,
            "delivery_days": 30
        }
        response = requests.post(f"{BASE_URL}/api/contractors/submit-offer", json=offer_data)
        assert response.status_code in [401, 403]
        print("Unauthenticated offer submission rejected")


class TestIntegrationFlows:
    """Integration tests for complete flows"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_full_verification_flow(self):
        """Test complete verification flow"""
        # 1. Submit verification data
        verification_data = {
            "full_name": "Интеграционный Тест",
            "passport_series": "AB",
            "passport_number": "9999999",
            "passport_issued_by": "Тестовым ГОВД",
            "passport_issue_date": "2020-01-01",
            "registration_address": "г. Тест, ул. Тестовая, д. 1",
            "phone": "+375299999999",
            "email": TEST_USER_EMAIL,
            "client_type": "individual"
        }
        
        submit_response = requests.post(f"{BASE_URL}/api/verification/submit",
                                       json=verification_data, headers=self.headers)
        assert submit_response.status_code == 200
        contract_number = submit_response.json()["contract_number"]
        print(f"Step 1: Verification submitted - {contract_number}")
        
        # 2. Check status
        status_response = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "pending"
        print("Step 2: Status is pending")
        
        # 3. Upload documents
        doc_data = {
            "doc_type": "passport_scan",
            "file_url": "https://example.com/passport.jpg",
            "file_name": "passport.jpg"
        }
        upload_response = requests.post(f"{BASE_URL}/api/verification/upload-document",
                                       json=doc_data, headers=self.headers)
        assert upload_response.status_code == 200
        print("Step 3: Document uploaded")
        
        # 4. Get contract
        contract_response = requests.get(f"{BASE_URL}/api/verification/contract", headers=self.headers)
        assert contract_response.status_code == 200
        assert contract_response.json()["contract_number"] == contract_number
        print("Step 4: Contract retrieved")
        
        # 5. Sign contract
        sign_response = requests.post(f"{BASE_URL}/api/verification/sign-contract",
                                     json={}, headers=self.headers)
        assert sign_response.status_code == 200
        print("Step 5: Contract signed")
        
        # 6. Verify final status
        final_status = requests.get(f"{BASE_URL}/api/verification/status", headers=self.headers)
        assert final_status.status_code == 200
        assert final_status.json()["status"] == "under_review"
        print("Step 6: Status is under_review - Flow complete!")
    
    def test_full_application_flow(self):
        """Test complete application flow"""
        # 1. Create application
        app_data = {
            "client_type": "individual",
            "full_name": "Тест Полного Потока",
            "phone": "+375291234567",
            "email": TEST_USER_EMAIL,
            "preferred_contact": "telegram",
            "brand": "Zeekr",
            "model": "001",
            "engine_type": "electric",
            "budget_max": 60000,
            "budget_currency": "USD"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/applications/create",
                                       json=app_data, headers=self.headers)
        assert create_response.status_code == 200
        app_id = create_response.json()["application_id"]
        app_number = create_response.json()["application_number"]
        print(f"Step 1: Application created - {app_number}")
        
        # 2. Get application
        get_response = requests.get(f"{BASE_URL}/api/applications/{app_id}", headers=self.headers)
        assert get_response.status_code == 200
        assert get_response.json()["brand"] == "Zeekr"
        print("Step 2: Application retrieved")
        
        # 3. Get all applications
        list_response = requests.get(f"{BASE_URL}/api/applications/my", headers=self.headers)
        assert list_response.status_code == 200
        assert any(a["id"] == app_id for a in list_response.json())
        print("Step 3: Application in list")
        
        # 4. Cancel application
        cancel_response = requests.delete(f"{BASE_URL}/api/applications/{app_id}", headers=self.headers)
        assert cancel_response.status_code == 200
        print("Step 4: Application cancelled - Flow complete!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
