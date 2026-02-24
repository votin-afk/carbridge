import requests
import sys
import json
from datetime import datetime

class CarbridgeAPITester:
    def __init__(self, base_url="https://concept-site.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            details = ""
            
            if not success:
                details = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   Error: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_health_check(self):
        """Test basic API health"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_register_user(self):
        """Test user registration"""
        test_email = f"test_{datetime.now().strftime('%H%M%S')}@carbridge.by"
        user_data = {
            "email": test_email,
            "password": "password123",
            "name": "Test User",
            "phone": "+375291234567",
            "user_type": "individual"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_login_user(self):
        """Test user login with existing credentials"""
        login_data = {
            "email": "test@carbridge.by",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "User Login", 
            "POST", 
            "auth/login", 
            200, 
            login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_get_user_profile(self):
        """Test getting current user profile"""
        return self.run_test("Get User Profile", "GET", "auth/me", 200)

    def test_calculator(self):
        """Test customs calculator"""
        calc_data = {
            "price_cny": 150000,
            "age": "under3",
            "engine_type": "electric",
            "user_type": "individual"
        }
        
        success, response = self.run_test(
            "Calculator - Electric Individual", 
            "POST", 
            "calculator", 
            200, 
            calc_data
        )
        
        if success:
            # Verify response structure
            required_fields = ['total_usd', 'total_byn', 'customs_duty', 'utilization_fee']
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                self.log_test("Calculator Response Structure", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Calculator Response Structure", True)
                print(f"   Total USD: ${response.get('total_usd', 0):,.2f}")
                print(f"   Total BYN: {response.get('total_byn', 0):,.2f} BYN")
        
        return success

    def test_add_car_to_garage(self):
        """Test adding a car to garage"""
        car_data = {
            "brand": "BYD",
            "model": "Han EV",
            "year": 2023,
            "price_cny": 280000,
            "engine_type": "electric",
            "mileage": 5000,
            "description": "Test car for API testing"
        }
        
        success, response = self.run_test(
            "Add Car to Garage", 
            "POST", 
            "garage", 
            200, 
            car_data
        )
        
        if success and 'id' in response:
            self.car_id = response['id']
            print(f"   Car ID: {self.car_id}")
            return True
        return False

    def test_get_garage(self):
        """Test getting garage cars"""
        return self.run_test("Get Garage", "GET", "garage", 200)

    def test_create_tender(self):
        """Test creating a tender"""
        if not hasattr(self, 'car_id'):
            self.log_test("Create Tender", False, "No car_id available")
            return False
            
        tender_data = {"car_id": self.car_id}
        
        success, response = self.run_test(
            "Create Tender", 
            "POST", 
            "tenders", 
            200, 
            tender_data
        )
        
        if success and 'id' in response:
            self.tender_id = response['id']
            print(f"   Tender ID: {self.tender_id}")
            print(f"   Offers count: {len(response.get('offers', []))}")
            return True
        return False

    def test_get_tenders(self):
        """Test getting tenders"""
        return self.run_test("Get Tenders", "GET", "tenders", 200)

    def test_ai_chat(self):
        """Test AI chat functionality"""
        chat_data = {
            "message": "Привет! Помоги подобрать электромобиль до $30000",
            "session_id": "test_session_123"
        }
        
        success, response = self.run_test(
            "AI Chat", 
            "POST", 
            "chat", 
            200, 
            chat_data
        )
        
        if success and 'response' in response:
            print(f"   AI Response: {response['response'][:100]}...")
            return True
        return False

    def test_exchange_rates(self):
        """Test exchange rates endpoint"""
        return self.run_test("Exchange Rates", "GET", "exchange-rates", 200)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting CARBRIDGE API Tests")
        print("=" * 50)
        
        # Basic health check
        self.test_health_check()
        
        # Authentication tests
        auth_success = self.test_register_user() or self.test_login_user()
        if not auth_success:
            print("\n❌ Authentication failed - stopping tests")
            return self.generate_report()
        
        self.test_get_user_profile()
        
        # Calculator test (no auth required)
        self.test_calculator()
        self.test_exchange_rates()
        
        # Garage tests (auth required)
        self.test_add_car_to_garage()
        self.test_get_garage()
        
        # Tender tests (auth required)
        self.test_create_tender()
        self.test_get_tenders()
        
        # AI Chat test
        self.test_ai_chat()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
            return 1

def main():
    tester = CarbridgeAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())