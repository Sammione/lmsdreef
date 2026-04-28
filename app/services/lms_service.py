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
            "Authorization": f"{settings.lms_api_key}",
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

    async def get_courses(self, search: str = None, page_size: int = 10):
        url = f"{self.base_url}/api/v1/Course"
        params = {"PageSize": page_size}
        if search:
            params["Search"] = search
        
        client = await self.get_client()
        try:
            logger.info(f"Fetching courses from LMS: {url} with params {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching courses from LMS: {str(e)}")
            return {"error": "LMS service unavailable", "details": str(e)}

    async def get_course_details(self, course_id: str):
        url = f"{self.base_url}/api/v1/Course/{course_id}"
        client = await self.get_client()
        try:
            logger.info(f"Fetching course details from LMS: {url}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching course details from LMS: {str(e)}")
            return {"error": f"Course {course_id} not found or LMS unavailable", "details": str(e)}

    async def get_assessments(self, course_id: str):
        # Using the course full structure endpoint as direct Assessment GET is not available
        url = f"{self.base_url}/api/v1/Course/{course_id}/full"
        client = await self.get_client()
        try:
            logger.info(f"Fetching full course structure (including assessments) from LMS: {url}")
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            # Extract assessments if needed, or just return the whole structure
            return data
        except Exception as e:
            logger.error(f"Error fetching course structure: {str(e)}")
            return {"error": "Course structure unavailable", "details": str(e)}

    async def get_my_certificates(self):
        url = f"{self.base_url}/api/v1/Certificate"
        client = await self.get_client()
        try:
            logger.info(f"Fetching certificates from LMS")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching certificates: {str(e)}")
            return {"error": "Certificates unavailable", "details": str(e)}

    # New Chatbot-specific Endpoints
    async def get_overall_stats(self):
        url = f"{self.base_url}/api/v1/chatbot/stats/overall"
        client = await self.get_client()
        try:
            logger.info(f"Fetching overall platform stats")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching overall stats: {str(e)}")
            return {"error": "Stats unavailable", "details": str(e)}

    async def get_course_faqs(self, course_id: str):
        url = f"{self.base_url}/api/v1/chatbot/courses/{course_id}/faqs"
        client = await self.get_client()
        try:
            logger.info(f"Fetching FAQs for course {course_id}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching FAQs: {str(e)}")
            return {"error": "FAQs unavailable", "details": str(e)}

    async def get_course_glossary(self, course_id: str):
        url = f"{self.base_url}/api/v1/chatbot/courses/{course_id}/glossary"
        client = await self.get_client()
        try:
            logger.info(f"Fetching glossary for course {course_id}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching glossary: {str(e)}")
            return {"error": "Glossary unavailable", "details": str(e)}

    async def get_course_sops(self, course_id: str):
        url = f"{self.base_url}/api/v1/chatbot/courses/{course_id}/sops"
        client = await self.get_client()
        try:
            logger.info(f"Fetching SOPs for course {course_id}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SOPs: {str(e)}")
            return {"error": "SOPs unavailable", "details": str(e)}

    async def get_course_materials(self, course_id: str):
        url = f"{self.base_url}/api/v1/chatbot/courses/{course_id}/materials"
        client = await self.get_client()
        try:
            logger.info(f"Fetching materials for course {course_id}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching materials: {str(e)}")
            return {"error": "Materials unavailable", "details": str(e)}

    async def get_per_course_stats(self):
        url = f"{self.base_url}/api/v1/chatbot/stats/per-course"
        client = await self.get_client()
        try:
            logger.info(f"Fetching per-course completion stats")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching per-course stats: {str(e)}")
            return {"error": "Per-course stats unavailable", "details": str(e)}

    async def get_monthly_enrollments(self, months: int = 6):
        url = f"{self.base_url}/api/v1/chatbot/stats/monthly-enrollments"
        params = {"months": months}
        client = await self.get_client()
        try:
            logger.info(f"Fetching monthly enrollment counts for last {months} months")
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching monthly enrollments: {str(e)}")
            return {"error": "Monthly enrollments unavailable", "details": str(e)}

    async def get_chatbot_course_details(self, course_id: str):
        url = f"{self.base_url}/api/v1/chatbot/courses/{course_id}"
        client = await self.get_client()
        try:
            logger.info(f"Fetching full chatbot-specific course structure for {course_id}")
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching chatbot course details: {str(e)}")
            return {"error": "Chatbot-specific course details unavailable", "details": str(e)}

# Singleton instance for better resource management
_lms_client_instance = LMSClient()

def get_lms_client():
    return _lms_client_instance

