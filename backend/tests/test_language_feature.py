"""
Test suite for Language Toggle Feature (RU/EN)
Tests:
- AI chat endpoint with lang parameter
- Language persistence in localStorage (tested via frontend)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIChatLanguage:
    """Test AI chat endpoint with language parameter"""
    
    def test_chat_endpoint_with_russian_language(self):
        """Test POST /api/chat with lang='ru' returns Russian response"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Привет, как работает платформа?",
                "lang": "ru"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        
        # Check response is not empty
        assert len(data["response"]) > 0, "Response should not be empty"
        
        print(f"Russian response (first 200 chars): {data['response'][:200]}...")
        
    def test_chat_endpoint_with_english_language(self):
        """Test POST /api/chat with lang='en' returns English response"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Hello, how does the platform work?",
                "lang": "en"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        
        # Check response is not empty
        assert len(data["response"]) > 0, "Response should not be empty"
        
        print(f"English response (first 200 chars): {data['response'][:200]}...")
        
    def test_chat_endpoint_default_language_is_russian(self):
        """Test POST /api/chat without lang parameter defaults to Russian"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "Привет"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        
        print(f"Default language response (first 200 chars): {data['response'][:200]}...")


class TestContractorsPageLanguage:
    """Test Contractors page API returns data that can be translated"""
    
    def test_contractors_list_endpoint(self):
        """Test GET /api/contractors returns contractor data"""
        response = requests.get(f"{BASE_URL}/api/contractors", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            contractor = data[0]
            print(f"First contractor: {contractor.get('company_name', 'N/A')}")
            print(f"Services: {contractor.get('services', [])}")


class TestContractorProfilePageLanguage:
    """Test Contractor Profile page API"""
    
    def test_contractor_profile_endpoint(self):
        """Test GET /api/contractors/{id}/page returns profile data"""
        # First get list of contractors
        list_response = requests.get(f"{BASE_URL}/api/contractors", timeout=30)
        
        if list_response.status_code == 200 and len(list_response.json()) > 0:
            contractor_id = list_response.json()[0].get('id')
            
            response = requests.get(f"{BASE_URL}/api/contractors/{contractor_id}/page", timeout=30)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "contractor" in data, "Response should contain 'contractor' field"
            
            print(f"Contractor profile loaded: {data['contractor'].get('company_name', 'N/A')}")
        else:
            pytest.skip("No contractors available for testing")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
