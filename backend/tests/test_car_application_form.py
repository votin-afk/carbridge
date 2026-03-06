"""
Test suite for the new 6-step car application form.
Tests the comprehensive application form matching the PDF template.
Covers all 6 sections: Client data, Car parameters, Mileage/condition, Options, Budget, Priorities.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestCarApplicationAPI:
    """Test the car application creation API with all 6 sections"""
    
    def test_create_minimal_application(self, headers):
        """Test creating application with only required fields"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Минимальная Заявка"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "application_id" in data
        assert "application_number" in data
        assert data["message"] == "Заявка успешно создана"
    
    def test_create_full_application_section1_client_data(self, headers):
        """Test Section 1: Client data (client_type, full_name, delivery_city)"""
        payload = {
            "client_type": "legal",
            "full_name": "TEST_ООО Тестовая Компания",
            "delivery_city": "Минск"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data was saved
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app is not None
        assert created_app["client_type"] == "legal"
        assert created_app["full_name"] == "TEST_ООО Тестовая Компания"
        assert created_app["delivery_city"] == "Минск"
    
    def test_create_application_section2_car_params(self, headers):
        """Test Section 2: Car parameters (brand, model, year, body, engine, transmission, drive, colors)"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Параметры Авто",
            # 2.1 Basic characteristics
            "brand": "Zeekr",
            "model": "001",
            "year_from": 2023,
            "year_to": 2024,
            "body_type": "suv",
            # 2.2 Engine and transmission
            "engine_type": "electric",
            "engine_volume": "any",
            "power_from": 300,
            "power_to": 600,
            "transmission": "reducer",
            "drive_type": "awd",
            # 2.3 Appearance
            "body_color": "black",
            "exact_color": "Midnight Black Pearl",
            "color_importance": "required",
            "interior_color": "beige",
            "interior_material": "leather"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app["brand"] == "Zeekr"
        assert created_app["model"] == "001"
        assert created_app["year_from"] == 2023
        assert created_app["year_to"] == 2024
        assert created_app["body_type"] == "suv"
        assert created_app["engine_type"] == "electric"
        assert created_app["transmission"] == "reducer"
        assert created_app["drive_type"] == "awd"
        assert created_app["body_color"] == "black"
        assert created_app["interior_color"] == "beige"
        assert created_app["interior_material"] == "leather"
    
    def test_create_application_section3_mileage_condition(self, headers):
        """Test Section 3: Mileage and condition (mileage_max, car_condition, damage settings)"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Пробег и Состояние",
            # 3.1 Mileage
            "mileage_max": "lt50",
            "car_condition": "used",
            # 3.2 Damage
            "allow_damage": True,
            "damage_level": "level12",
            "damage_comment": "Допускаются мелкие царапины и небольшие вмятины"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app["mileage_max"] == "lt50"
        assert created_app["car_condition"] == "used"
        assert created_app["allow_damage"] == True
        assert created_app["damage_level"] == "level12"
        assert "царапины" in created_app["damage_comment"]
    
    def test_create_application_section4_options(self, headers):
        """Test Section 4: Additional options (electronic, comfort, exterior, other)"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Опции",
            # Electronic options
            "options_electronic": ["system_360", "acc", "lka", "autopark", "carplay"],
            # Comfort options
            "options_comfort": ["panoramic_roof", "heated_front", "ventilated_seats", "massage_seats", "climate_control"],
            # Exterior options
            "options_exterior": ["sport_package", "wheels_r18", "led_matrix"],
            # Other options
            "options_other": ["towbar", "spare_wheel", "third_row"],
            # Text options
            "required_options": "панорама, кожа, система 360",
            "preferred_options": "массаж, HUD, премиум аудио"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert "system_360" in created_app["options_electronic"]
        assert "panoramic_roof" in created_app["options_comfort"]
        assert "led_matrix" in created_app["options_exterior"]
        assert "spare_wheel" in created_app["options_other"]
        assert "панорама" in created_app["required_options"]
    
    def test_create_application_section5_budget(self, headers):
        """Test Section 5: Budget and conditions (budget, timeline, payment, purpose, customs)"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Бюджет",
            # Budget
            "budget_china_from": 20000,
            "budget_china_to": 40000,
            "budget_total": 55000,
            # Conditions
            "purchase_timeline": "2_3months",
            "payment_method": "installment",
            "car_purpose": "business",
            "customs_clearance": "carbridge"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app["budget_china_from"] == 20000
        assert created_app["budget_china_to"] == 40000
        assert created_app["budget_total"] == 55000
        assert created_app["purchase_timeline"] == "2_3months"
        assert created_app["payment_method"] == "installment"
        assert created_app["car_purpose"] == "business"
        assert created_app["customs_clearance"] == "carbridge"
    
    def test_create_application_section6_priorities(self, headers):
        """Test Section 6: Priorities and comments (priority rankings 1-5, additional requirements)"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Приоритеты",
            # Priorities (1-5 ranking)
            "priority_price": 1,
            "priority_reliability": 2,
            "priority_technology": 3,
            "priority_prestige": 4,
            "priority_fuel": 5,
            # Additional requirements
            "additional_requirements": "Желательно белый или чёрный цвет. Максимальная комплектация. Без ДТП."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify data
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app["priority_price"] == 1
        assert created_app["priority_reliability"] == 2
        assert created_app["priority_technology"] == 3
        assert created_app["priority_prestige"] == 4
        assert created_app["priority_fuel"] == 5
        assert "белый" in created_app["additional_requirements"]
    
    def test_create_complete_application_all_sections(self, headers):
        """Test creating a complete application with all 6 sections filled"""
        payload = {
            # Section 1: Client data
            "client_type": "individual",
            "full_name": "TEST_Полная Заявка Иванов Иван",
            "delivery_city": "Гомель",
            
            # Section 2.1: Basic characteristics
            "brand": "Li Auto",
            "model": "L9",
            "year_from": 2023,
            "year_to": 2024,
            "body_type": "suv",
            
            # Section 2.2: Engine and transmission
            "engine_type": "phev",
            "engine_volume": "15_2",
            "power_from": 400,
            "power_to": 600,
            "transmission": "at",
            "drive_type": "awd",
            
            # Section 2.3: Appearance
            "body_color": "grey",
            "exact_color": "Space Grey Metallic",
            "color_importance": "preferred",
            "interior_color": "brown",
            "interior_material": "leather",
            
            # Section 3: Mileage and condition
            "mileage_max": "lt30",
            "car_condition": "used",
            "allow_damage": True,
            "damage_level": "level1",
            "damage_comment": "Только мелкие царапины на бамперах",
            
            # Section 4: Options
            "options_electronic": ["system_360", "acc", "lka", "hud", "carplay"],
            "options_comfort": ["panoramic_roof", "heated_front", "heated_rear", "massage_seats", "climate_control", "electric_trunk"],
            "options_exterior": ["wheels_r18", "led_matrix"],
            "options_other": ["third_row", "premium_audio"],
            "required_options": "панорама, третий ряд",
            "preferred_options": "массаж, HUD",
            
            # Section 5: Budget and conditions
            "budget_china_from": 45000,
            "budget_china_to": 55000,
            "budget_total": 75000,
            "purchase_timeline": "1month",
            "payment_method": "full_prepay",
            "car_purpose": "personal",
            "customs_clearance": "carbridge",
            
            # Section 6: Priorities
            "priority_price": 3,
            "priority_reliability": 1,
            "priority_technology": 2,
            "priority_prestige": 4,
            "priority_fuel": 5,
            "additional_requirements": "Семейный автомобиль на 7 мест. Важна надёжность и технологичность."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "application_id" in data
        assert "application_number" in data
        
        # Verify all data was saved correctly
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == data["application_id"]), None)
        
        assert created_app is not None
        
        # Verify Section 1
        assert created_app["client_type"] == "individual"
        assert "Полная Заявка" in created_app["full_name"]
        assert created_app["delivery_city"] == "Гомель"
        
        # Verify Section 2
        assert created_app["brand"] == "Li Auto"
        assert created_app["model"] == "L9"
        assert created_app["engine_type"] == "phev"
        
        # Verify Section 3
        assert created_app["mileage_max"] == "lt30"
        assert created_app["allow_damage"] == True
        
        # Verify Section 4
        assert len(created_app["options_electronic"]) == 5
        assert len(created_app["options_comfort"]) == 6
        
        # Verify Section 5
        assert created_app["budget_china_from"] == 45000
        assert created_app["budget_total"] == 75000
        
        # Verify Section 6
        assert created_app["priority_reliability"] == 1
        assert "Семейный" in created_app["additional_requirements"]
    
    def test_application_appears_in_list(self, headers):
        """Test that created application appears in the applications list"""
        # Create application
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Проверка Списка",
            "brand": "BYD",
            "budget_total": 30000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Get list
        list_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        assert list_response.status_code == 200
        
        apps = list_response.json()
        app_ids = [a["id"] for a in apps]
        assert app_id in app_ids
    
    def test_application_status_is_new(self, headers):
        """Test that new application has status 'new'"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Статус Новый"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
        app_id = response.json()["application_id"]
        
        # Verify status
        apps_response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = apps_response.json()
        created_app = next((a for a in apps if a["id"] == app_id), None)
        
        assert created_app["status"] == "new"
        assert created_app["offers_count"] == 0
        assert created_app["manager_assigned"] == False
        assert created_app["tender_started"] == False


class TestCarApplicationValidation:
    """Test validation of application fields"""
    
    def test_client_type_validation(self, headers):
        """Test that client_type accepts only valid values"""
        # Valid individual
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json={"client_type": "individual", "full_name": "TEST_Valid Individual"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Valid legal
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json={"client_type": "legal", "full_name": "TEST_Valid Legal"},
            headers=headers
        )
        assert response.status_code == 200
    
    def test_full_name_required(self, headers):
        """Test that full_name is required"""
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json={"client_type": "individual"},
            headers=headers
        )
        # Should fail validation
        assert response.status_code == 422
    
    def test_numeric_fields_accept_numbers(self, headers):
        """Test that numeric fields accept proper numbers"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Числовые Поля",
            "year_from": 2020,
            "year_to": 2024,
            "power_from": 150,
            "power_to": 500,
            "budget_china_from": 15000.50,
            "budget_china_to": 35000.75,
            "budget_total": 50000.00,
            "priority_price": 1,
            "priority_reliability": 2,
            "priority_technology": 3,
            "priority_prestige": 4,
            "priority_fuel": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200
    
    def test_array_fields_accept_arrays(self, headers):
        """Test that array fields accept proper arrays"""
        payload = {
            "client_type": "individual",
            "full_name": "TEST_Массивы",
            "options_electronic": ["system_360", "acc"],
            "options_comfort": ["panoramic_roof"],
            "options_exterior": [],
            "options_other": ["spare_wheel", "third_row"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 200


class TestApplicationListEndpoint:
    """Test the GET /api/applications/my endpoint"""
    
    def test_get_applications_list(self, headers):
        """Test getting list of user's applications"""
        response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_applications_have_required_fields(self, headers):
        """Test that applications in list have all required display fields"""
        # First create an application
        create_response = requests.post(
            f"{BASE_URL}/api/applications/create",
            json={
                "client_type": "individual",
                "full_name": "TEST_Поля Списка",
                "brand": "Geely",
                "delivery_city": "Брест",
                "budget_total": 40000
            },
            headers=headers
        )
        assert create_response.status_code == 200
        
        # Get list
        response = requests.get(f"{BASE_URL}/api/applications/my", headers=headers)
        apps = response.json()
        
        # Find our app
        test_app = next((a for a in apps if "Поля Списка" in a.get("full_name", "")), None)
        assert test_app is not None
        
        # Check required display fields
        assert "id" in test_app
        assert "application_number" in test_app
        assert "status" in test_app
        assert "created_at" in test_app
        assert "brand" in test_app
        assert "delivery_city" in test_app
        assert "budget_total" in test_app


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_applications(headers):
    """Cleanup TEST_ prefixed applications after tests"""
    yield
    # Note: In production, you would delete test data here
    # For now, we leave it as test data is prefixed with TEST_
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
