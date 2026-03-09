"""
Bitrix24 CRM Integration Service
Full REST API integration for CarBridge platform
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


class Bitrix24Service:
    """Service for Bitrix24 CRM integration"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Bitrix24 service
        
        Args:
            webhook_url: Bitrix24 REST API webhook URL
        """
        self.webhook_url = webhook_url.rstrip('/')
        self.timeout = 30.0
    
    async def _make_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Bitrix24 REST API"""
        url = f"{self.webhook_url}/{method}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=params or {})
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(f"Bitrix24 API error: {data['error']} - {data.get('error_description', '')}")
                    return {"success": False, "error": data.get("error_description", data["error"])}
                
                return {"success": True, "result": data.get("result")}
        except httpx.HTTPStatusError as e:
            logger.error(f"Bitrix24 HTTP error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Bitrix24 request error: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== CONTACTS ====================
    
    async def create_contact(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        user_type: str = "individual",
        user_id: Optional[str] = None,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create contact in Bitrix24 CRM
        
        Args:
            name: Contact full name
            email: Contact email
            phone: Contact phone number
            user_type: User type (individual/legal)
            user_id: Internal user ID for reference
            comments: Additional comments
        """
        # Split name into parts
        name_parts = name.split() if name else [""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        params = {
            "fields": {
                "NAME": first_name,
                "LAST_NAME": last_name,
                "TYPE_ID": "CLIENT",
                "SOURCE_ID": "WEB",
                "OPENED": "Y",
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "COMMENTS": comments or f"Зарегистрирован на CarBridge. Тип: {user_type}. ID: {user_id}"
            }
        }
        
        if phone:
            params["fields"]["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "MOBILE"}]
        
        # Custom field for user type
        params["fields"]["UF_CRM_USER_TYPE"] = user_type
        params["fields"]["UF_CRM_CARBRIDGE_ID"] = user_id
        
        result = await self._make_request("crm.contact.add", params)
        
        if result["success"]:
            logger.info(f"Created Bitrix24 contact: {result['result']} for {email}")
        
        return result
    
    async def find_contact_by_email(self, email: str) -> Optional[int]:
        """Find contact by email, return contact ID if found"""
        params = {
            "filter": {"EMAIL": email},
            "select": ["ID", "NAME", "EMAIL"]
        }
        
        result = await self._make_request("crm.contact.list", params)
        
        if result["success"] and result["result"]:
            return int(result["result"][0]["ID"])
        
        return None
    
    async def update_contact(self, contact_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact"""
        params = {
            "id": contact_id,
            "fields": fields
        }
        return await self._make_request("crm.contact.update", params)
    
    # ==================== LEADS ====================
    
    async def create_lead(
        self,
        title: str,
        contact_name: str,
        email: str,
        phone: Optional[str] = None,
        car_brand: Optional[str] = None,
        car_model: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        application_id: Optional[str] = None,
        comments: Optional[str] = None,
        source: str = "Заявка на авто"
    ) -> Dict[str, Any]:
        """
        Create lead in Bitrix24 CRM (for new car applications)
        
        Args:
            title: Lead title
            contact_name: Contact name
            email: Contact email
            phone: Contact phone
            car_brand: Desired car brand
            car_model: Desired car model
            budget_min: Minimum budget
            budget_max: Maximum budget
            application_id: Internal application ID
            comments: Additional comments
            source: Lead source description
        """
        # Build lead title
        lead_title = title or f"Заявка на {car_brand or 'авто'} {car_model or ''} от {contact_name}"
        
        # Build description
        description_parts = [
            f"Источник: {source}",
            f"Клиент: {contact_name}",
            f"Email: {email}",
        ]
        if phone:
            description_parts.append(f"Телефон: {phone}")
        if car_brand:
            description_parts.append(f"Марка: {car_brand}")
        if car_model:
            description_parts.append(f"Модель: {car_model}")
        if budget_min or budget_max:
            description_parts.append(f"Бюджет: ${budget_min or 0} - ${budget_max or '∞'}")
        if application_id:
            description_parts.append(f"ID заявки: {application_id}")
        if comments:
            description_parts.append(f"Комментарий: {comments}")
        
        params = {
            "fields": {
                "TITLE": lead_title,
                "NAME": contact_name.split()[0] if contact_name else "",
                "LAST_NAME": " ".join(contact_name.split()[1:]) if contact_name and len(contact_name.split()) > 1 else "",
                "STATUS_ID": "NEW",
                "OPENED": "Y",
                "SOURCE_ID": "WEB",
                "SOURCE_DESCRIPTION": "CarBridge - импорт авто из Китая",
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "COMMENTS": "\n".join(description_parts),
                "CURRENCY_ID": "USD",
                "OPPORTUNITY": budget_max or budget_min or 0,
                # Custom fields
                "UF_CRM_CAR_BRAND": car_brand,
                "UF_CRM_CAR_MODEL": car_model,
                "UF_CRM_BUDGET_MIN": budget_min,
                "UF_CRM_BUDGET_MAX": budget_max,
                "UF_CRM_APPLICATION_ID": application_id
            }
        }
        
        if phone:
            params["fields"]["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "MOBILE"}]
        
        result = await self._make_request("crm.lead.add", params)
        
        if result["success"]:
            logger.info(f"Created Bitrix24 lead: {result['result']} - {lead_title}")
        
        return result
    
    async def update_lead_status(self, lead_id: int, status: str) -> Dict[str, Any]:
        """Update lead status"""
        # Bitrix24 lead statuses: NEW, IN_PROCESS, PROCESSED, CONVERTED, JUNK
        status_map = {
            "new": "NEW",
            "in_progress": "IN_PROCESS", 
            "processed": "PROCESSED",
            "converted": "CONVERTED",
            "rejected": "JUNK"
        }
        
        params = {
            "id": lead_id,
            "fields": {
                "STATUS_ID": status_map.get(status, "IN_PROCESS")
            }
        }
        return await self._make_request("crm.lead.update", params)
    
    # ==================== DEALS ====================
    
    async def create_deal(
        self,
        title: str,
        contact_id: Optional[int] = None,
        contact_email: Optional[str] = None,
        car_brand: Optional[str] = None,
        car_model: Optional[str] = None,
        car_year: Optional[int] = None,
        price_usd: Optional[float] = None,
        tender_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        contractor_name: Optional[str] = None,
        stage: str = "NEW",
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create deal in Bitrix24 CRM (for tenders and deals)
        
        Args:
            title: Deal title
            contact_id: Bitrix24 contact ID
            contact_email: Contact email (to find/create contact)
            car_brand: Car brand
            car_model: Car model
            car_year: Car year
            price_usd: Deal amount in USD
            tender_id: Internal tender ID
            deal_id: Internal deal ID
            contractor_name: Assigned contractor name
            stage: Deal stage
            comments: Additional comments
        """
        # Find or use contact
        if not contact_id and contact_email:
            contact_id = await self.find_contact_by_email(contact_email)
        
        # Build deal title
        deal_title = title or f"Сделка: {car_brand or ''} {car_model or ''} {car_year or ''}"
        
        # Build description
        description_parts = []
        if car_brand:
            description_parts.append(f"Марка: {car_brand}")
        if car_model:
            description_parts.append(f"Модель: {car_model}")
        if car_year:
            description_parts.append(f"Год: {car_year}")
        if contractor_name:
            description_parts.append(f"Подрядчик: {contractor_name}")
        if tender_id:
            description_parts.append(f"ID тендера: {tender_id}")
        if deal_id:
            description_parts.append(f"ID сделки: {deal_id}")
        if comments:
            description_parts.append(f"Комментарий: {comments}")
        
        # Map stage to Bitrix24 deal stages
        stage_map = {
            "NEW": "NEW",
            "PREPARATION": "PREPARATION",
            "PREPAYMENT_INVOICE": "PREPAYMENT_INVOICE", 
            "EXECUTING": "EXECUTING",
            "FINAL_INVOICE": "FINAL_INVOICE",
            "WON": "WON",
            "LOSE": "LOSE",
            "new": "NEW",
            "in_progress": "EXECUTING",
            "completed": "WON",
            "cancelled": "LOSE"
        }
        
        params = {
            "fields": {
                "TITLE": deal_title,
                "STAGE_ID": stage_map.get(stage, "NEW"),
                "OPENED": "Y",
                "CURRENCY_ID": "USD",
                "OPPORTUNITY": price_usd or 0,
                "SOURCE_ID": "WEB",
                "SOURCE_DESCRIPTION": "CarBridge - импорт авто из Китая",
                "COMMENTS": "\n".join(description_parts),
                # Custom fields
                "UF_CRM_CAR_BRAND": car_brand,
                "UF_CRM_CAR_MODEL": car_model,
                "UF_CRM_CAR_YEAR": car_year,
                "UF_CRM_TENDER_ID": tender_id,
                "UF_CRM_DEAL_ID": deal_id,
                "UF_CRM_CONTRACTOR": contractor_name
            }
        }
        
        if contact_id:
            params["fields"]["CONTACT_ID"] = contact_id
        
        result = await self._make_request("crm.deal.add", params)
        
        if result["success"]:
            logger.info(f"Created Bitrix24 deal: {result['result']} - {deal_title}")
        
        return result
    
    async def update_deal_stage(self, deal_id: int, stage: str) -> Dict[str, Any]:
        """Update deal stage"""
        stage_map = {
            "new": "NEW",
            "in_progress": "EXECUTING",
            "inspection": "PREPARATION",
            "export": "PREPAYMENT_INVOICE",
            "delivery": "EXECUTING",
            "customs": "FINAL_INVOICE",
            "completed": "WON",
            "cancelled": "LOSE"
        }
        
        params = {
            "id": deal_id,
            "fields": {
                "STAGE_ID": stage_map.get(stage, "EXECUTING")
            }
        }
        return await self._make_request("crm.deal.update", params)
    
    async def add_deal_comment(self, deal_id: int, comment: str) -> Dict[str, Any]:
        """Add comment/activity to deal"""
        params = {
            "fields": {
                "OWNER_TYPE_ID": 2,  # Deal
                "OWNER_ID": deal_id,
                "TYPE_ID": 6,  # Note/Comment
                "SUBJECT": "Обновление статуса",
                "DESCRIPTION": comment,
                "COMPLETED": "Y",
                "DIRECTION": 0,
                "COMMUNICATIONS": []
            }
        }
        return await self._make_request("crm.activity.add", params)
    
    # ==================== TASKS ====================
    
    async def create_task(
        self,
        title: str,
        description: str,
        responsible_id: int = 1,  # Default to admin
        deadline_days: int = 3,
        priority: int = 1,  # 0-low, 1-normal, 2-high
        deal_id: Optional[int] = None,
        contact_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create task in Bitrix24
        
        Args:
            title: Task title
            description: Task description
            responsible_id: Responsible user ID (default: 1 - admin)
            deadline_days: Days until deadline
            priority: Task priority (0-low, 1-normal, 2-high)
            deal_id: Related Bitrix24 deal ID
            contact_id: Related Bitrix24 contact ID
        """
        from datetime import timedelta
        
        deadline = (datetime.now(timezone.utc) + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
        
        params = {
            "fields": {
                "TITLE": title,
                "DESCRIPTION": description,
                "RESPONSIBLE_ID": responsible_id,
                "DEADLINE": deadline,
                "PRIORITY": priority,
                "ALLOW_CHANGE_DEADLINE": "Y",
                "TASK_CONTROL": "Y"
            }
        }
        
        # Link to CRM entities
        if deal_id:
            params["fields"]["UF_CRM_TASK"] = [f"D_{deal_id}"]
        if contact_id:
            if "UF_CRM_TASK" in params["fields"]:
                params["fields"]["UF_CRM_TASK"].append(f"C_{contact_id}")
            else:
                params["fields"]["UF_CRM_TASK"] = [f"C_{contact_id}"]
        
        result = await self._make_request("tasks.task.add", params)
        
        if result["success"]:
            logger.info(f"Created Bitrix24 task: {result['result']} - {title}")
        
        return result
    
    # ==================== NOTIFICATIONS ====================
    
    async def send_notification(
        self,
        user_id: int,
        message: str,
        message_type: str = "SYSTEM"
    ) -> Dict[str, Any]:
        """
        Send notification to Bitrix24 user
        
        Args:
            user_id: Bitrix24 user ID
            message: Notification message
            message_type: SYSTEM or PERSONAL
        """
        params = {
            "to": user_id,
            "message": message,
            "type": message_type
        }
        return await self._make_request("im.notify.system.add", params)
    
    async def send_chat_message(
        self,
        chat_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send message to Bitrix24 chat
        
        Args:
            chat_id: Chat ID (e.g., "chat123" or user ID for direct message)
            message: Message text
        """
        params = {
            "DIALOG_ID": chat_id,
            "MESSAGE": message
        }
        return await self._make_request("im.message.add", params)
    
    # ==================== PRODUCTS ====================
    
    async def add_product_to_deal(
        self,
        deal_id: int,
        product_name: str,
        price: float,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Add product row to deal"""
        params = {
            "id": deal_id,
            "rows": [{
                "PRODUCT_NAME": product_name,
                "PRICE": price,
                "QUANTITY": quantity
            }]
        }
        return await self._make_request("crm.deal.productrows.set", params)
    
    # ==================== UTILITY ====================
    
    async def get_user_list(self) -> Dict[str, Any]:
        """Get list of Bitrix24 users (for assigning tasks)"""
        return await self._make_request("user.get")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Bitrix24"""
        result = await self._make_request("app.info")
        if result["success"]:
            logger.info("Bitrix24 connection successful")
        return result


# Global instance (initialized in server.py)
bitrix24_service: Optional[Bitrix24Service] = None


def init_bitrix24(webhook_url: str) -> Bitrix24Service:
    """Initialize Bitrix24 service"""
    global bitrix24_service
    bitrix24_service = Bitrix24Service(webhook_url)
    return bitrix24_service


def get_bitrix24() -> Optional[Bitrix24Service]:
    """Get Bitrix24 service instance"""
    return bitrix24_service
