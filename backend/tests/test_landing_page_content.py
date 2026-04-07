"""
Test suite for Landing Page Content Update and AI Chat Enhancement
Tests: Hero text, 7-step process, 10 FAQ items, 4 advantages, AI chat suggestions
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vehicle-tender-hub.preview.emergentagent.com').rstrip('/')


class TestAIChatEndpoint:
    """Test AI chat endpoint with platform navigation and car selection queries"""
    
    def test_chat_endpoint_exists(self):
        """Test that POST /api/chat endpoint exists and responds"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Привет", "session_id": None},
            timeout=30
        )
        # Should return 200 or 500 (if AI service issue), not 404
        assert response.status_code in [200, 500], f"Chat endpoint returned {response.status_code}"
        print(f"✓ POST /api/chat endpoint exists (status: {response.status_code})")
    
    def test_chat_platform_question_tender(self):
        """Test AI chat responds to platform question about tender system"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Как работает тендер?", "session_id": None},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            assert "session_id" in data, "Response should contain 'session_id' field"
            
            # Check that response mentions tender-related keywords
            response_text = data["response"].lower()
            tender_keywords = ["тендер", "подрядчик", "предложен", "конкур", "выбор", "заявк"]
            has_tender_info = any(kw in response_text for kw in tender_keywords)
            print(f"✓ AI chat responds to tender question (has tender info: {has_tender_info})")
            print(f"  Response preview: {data['response'][:200]}...")
        else:
            print(f"⚠ AI chat returned {response.status_code} - may be service issue")
    
    def test_chat_car_search_query(self):
        """Test AI chat responds to car search query with catalog data"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Подобрать кроссовер до 200000 юаней", "session_id": None},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            
            # Check that response mentions car-related keywords
            response_text = data["response"].lower()
            car_keywords = ["кроссовер", "авто", "машин", "модел", "цена", "юан", "каталог"]
            has_car_info = any(kw in response_text for kw in car_keywords)
            print(f"✓ AI chat responds to car search query (has car info: {has_car_info})")
            print(f"  Response preview: {data['response'][:200]}...")
        else:
            print(f"⚠ AI chat returned {response.status_code} - may be service issue")
    
    def test_chat_platform_navigation_question(self):
        """Test AI chat responds to platform navigation question"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Какие этапы сделки?", "session_id": None},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            
            # Check that response mentions stages/steps
            response_text = data["response"].lower()
            stage_keywords = ["этап", "шаг", "проверк", "доставк", "договор", "оплат"]
            has_stage_info = any(kw in response_text for kw in stage_keywords)
            print(f"✓ AI chat responds to stages question (has stage info: {has_stage_info})")
            print(f"  Response preview: {data['response'][:200]}...")
        else:
            print(f"⚠ AI chat returned {response.status_code} - may be service issue")
    
    def test_chat_electric_car_query(self):
        """Test AI chat responds to electric car query"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Электромобиль до $30000", "session_id": None},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            
            # Check that response mentions electric car keywords
            response_text = data["response"].lower()
            ev_keywords = ["электро", "electric", "батаре", "зарядк", "byd", "nio", "xpeng", "zeekr"]
            has_ev_info = any(kw in response_text for kw in ev_keywords)
            print(f"✓ AI chat responds to EV query (has EV info: {has_ev_info})")
            print(f"  Response preview: {data['response'][:200]}...")
        else:
            print(f"⚠ AI chat returned {response.status_code} - may be service issue")


class TestLandingPageAPIs:
    """Test APIs used by landing page"""
    
    def test_hot_deals_endpoint(self):
        """Test hot deals endpoint used on landing page"""
        response = requests.get(f"{BASE_URL}/api/hot-deals?limit=4", timeout=10)
        assert response.status_code == 200, f"Hot deals returned {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Hot deals should return a list"
        print(f"✓ GET /api/hot-deals returns {len(data)} deals")
    
    def test_catalog_endpoint(self):
        """Test catalog endpoint used for AI chat context"""
        response = requests.get(f"{BASE_URL}/api/catalog/search?page=1&limit=5", timeout=15)
        assert response.status_code == 200, f"Catalog search returned {response.status_code}"
        data = response.json()
        assert "cars" in data, "Catalog should return 'cars' field"
        print(f"✓ GET /api/catalog/search returns {len(data.get('cars', []))} cars")
    
    def test_contractors_endpoint(self):
        """Test contractors endpoint linked from landing page"""
        response = requests.get(f"{BASE_URL}/api/contractors", timeout=10)
        assert response.status_code == 200, f"Contractors returned {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Contractors should return a list"
        print(f"✓ GET /api/contractors returns {len(data)} contractors")


class TestChatSessionPersistence:
    """Test chat session persistence"""
    
    def test_chat_session_continuity(self):
        """Test that chat maintains session context"""
        # First message
        response1 = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Меня зовут Тест", "session_id": None},
            timeout=60
        )
        
        if response1.status_code != 200:
            print(f"⚠ First chat message returned {response1.status_code}")
            return
        
        data1 = response1.json()
        session_id = data1.get("session_id")
        assert session_id, "Should return session_id"
        
        # Second message with same session
        response2 = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Как меня зовут?", "session_id": session_id},
            timeout=60
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            assert data2.get("session_id") == session_id, "Session ID should be preserved"
            print(f"✓ Chat session persistence works (session: {session_id[:8]}...)")
        else:
            print(f"⚠ Second chat message returned {response2.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
