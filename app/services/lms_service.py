import httpx
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LMSClient:
    _client = None

    def __init__(self):
        self.base_url = settings.lms_base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.lms_api_key}",
            "X-Api-Key": f"{settings.lms_api_key}",
            "X-Tenant-Key": settings.lms_tenant_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers
            )
        return self._client

    async def _make_request(self, method: str, path: str, params: dict = None, json_data: dict = None, token: str = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        client = await self.get_client()
        
        # Use provided user token if available, otherwise fallback to system settings
        request_headers = self.headers.copy()
        if token:
            if not token.startswith("Bearer "):
                token = f"Bearer {token}"
            request_headers["Authorization"] = token
            # Also update X-Api-Key if the system expects it to match
            request_headers["X-Api-Key"] = token.replace("Bearer ", "")

        try:
            logger.info(f"LMS Request: {method} {url} with params {params}")
            response = await client.request(
                method, 
                url, 
                params=params, 
                json=json_data, 
                headers=request_headers
            )
            
            if response.status_code >= 400:
                logger.error(f"LMS API Error: {method} {url} - Status {response.status_code}, Body: {response.text}")
                
            response.raise_for_status()
            data = response.json()
            
            # Log the number of items returned for debugging
            if isinstance(data, list):
                logger.info(f"LMS Response: {len(data)} items returned")
            elif isinstance(data, dict):
                inner_data = data.get("data", {})
                if isinstance(inner_data, dict) and "result" in inner_data:
                    results = inner_data["result"]
                    logger.info(f"LMS Response: {len(results)} items in 'data.result' (Total: {inner_data.get('totalRecords', 'unknown')})")
                else:
                    logger.info(f"LMS Response keys: {list(data.keys())}")
            
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error: {e.response.status_code} - {e.response.text}")
            return {"error": "LMS API Error", "status_code": e.response.status_code, "details": e.response.text}
        except Exception as e:
            logger.error(f"Unexpected error calling LMS: {str(e)}")
            return {"error": "LMS service unavailable", "details": str(e)}

    async def get_courses(self, search: str = None, page_size: int = 100, token: str = None):
        params = {"PageSize": page_size}
        if search:
            params["Search"] = search
        return await self._make_request("GET", "api/v1/Course", params=params, token=token)

    async def get_course_details(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/Course/{course_id}", token=token)

    async def get_assessments(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/Course/{course_id}/full", token=token)

    async def get_my_certificates(self, token: str = None):
        return await self._make_request("GET", "api/v1/Certificate", token=token)

    async def get_overall_stats(self, token: str = None):
        return await self._make_request("GET", "api/v1/chatbot/stats/overall", token=token)

    async def get_course_faqs(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/chatbot/courses/{course_id}/faqs", token=token)

    async def get_course_glossary(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/chatbot/courses/{course_id}/glossary", token=token)

    async def get_course_sops(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/chatbot/courses/{course_id}/sops", token=token)

    async def get_course_materials(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/chatbot/courses/{course_id}/materials", token=token)

    async def get_per_course_stats(self, token: str = None):
        return await self._make_request("GET", "api/v1/chatbot/stats/per-course", token=token)

    async def get_monthly_enrollments(self, months: int = 6, token: str = None):
        params = {"months": months}
        return await self._make_request("GET", "api/v1/chatbot/stats/monthly-enrollments", params=params, token=token)

    async def get_chatbot_course_details(self, course_id: str, token: str = None):
        return await self._make_request("GET", f"api/v1/chatbot/courses/{course_id}", token=token)

# Singleton instance for better resource management
_lms_client_instance = LMSClient()

def get_lms_client():
    return _lms_client_instance

