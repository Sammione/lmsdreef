from openai import AsyncOpenAI
from app.core.config import get_settings
import json
import os
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)


SYSTEM_PROMPT_UNIFIED = """
You are the Official LMS Assistant for InfraCredit. 
Your role is to provide a comprehensive support experience for all users on the LMS platform.

You can help with:
1. **Course Discovery**: Search for and provide details about available courses.
2. **Course Content & Structure**: Explain what is covered in specific courses, including modules and assessments.
3. **User Achievements**: Retrieve information about a user's certificates and completions.
4. **Platform Statistics**: Provide overall platform stats, per-course completion stats, or monthly enrollment trends.
5. **Course-Specific Resources**: Access FAQs, glossary terms, SOPs, and learning materials specifically for a course using the provided LMS tools.

**Strict Grounding Rules**:
1. **Source Only**: Answer questions ONLY using the information retrieved from the LMS tools (courses, certificates, stats, materials). 
2. **No Hallucination**: If the information is not explicitly present in the tool outputs, do NOT make up an answer.
3. **Unknown Information**: If you cannot find the answer, state clearly: "I'm sorry, I don't have that information in the LMS records. Please contact the HR or IT department for further assistance."
4. **Tool Priority**: Always prefer data from a tool call (like get_course_details) over your general training data regarding InfraCredit specific details.
5. **No Assumptions**: Do not assume course dates, costs, or requirements if they are not shown in the API response.

**Guidelines**:
- Be professional, factual, and concise.
- If a user asks about their own data (like certificates), use the get_my_certificates tool first.
"""

class OpenAIService:
    def __init__(self):
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_courses",
                    "description": "Get a list of available courses from the LMS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search": {"type": "string", "description": "Search term for courses"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_details",
                    "description": "Get detailed information about a specific course, including its structure and assessments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_assessments",
                    "description": "Get assessments and full structure for a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_my_certificates",
                    "description": "Get a list of certificates earned by the current user",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_overall_stats",
                    "description": "Get overall platform statistics including total learners, enrollments, and certificates",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_per_course_stats",
                    "description": "Get completion statistics for each course",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_monthly_enrollments",
                    "description": "Get monthly enrollment counts to see trends over time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "months": {"type": "integer", "description": "Number of months to look back (default 6)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_faqs",
                    "description": "Get Frequently Asked Questions specifically for a given course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_glossary",
                    "description": "Get glossary terms and definitions for a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_sops",
                    "description": "Get Standard Operating Procedures (SOPs) related to a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_course_materials",
                    "description": "Get learning materials (files, documents) for a specific course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "string", "description": "The unique ID of the course"}
                        },
                        "required": ["course_id"]
                    }
                }
            }
        ]

    async def chat(self, messages: list, bot_type: str = "unified", lms_client=None, user_token: str = None):
        system_prompt = SYSTEM_PROMPT_UNIFIED
        
        # Prepend system prompt if not present
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
            
        # First call to OpenAI to check for tool usage
        logger.info(f"Calling OpenAI (bot_type={bot_type}) with model: gpt-4o")
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools if lms_client else None,
                tool_choice="auto" if lms_client else None,
                temperature=0.0
            )
        except Exception as e:
            logger.error(f"OpenAI completion error (first call): {str(e)}")
            raise

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls and lms_client:
            logger.info(f"OpenAI requested tool calls: {[t.function.name for t in tool_calls]}")
            # Add the assistant's message with tool calls to history
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the appropriate LMS client method with the user token
                logger.info(f"Executing tool call: {function_name} with args: {function_args}")
                if function_name == "get_courses":
                    function_response = await lms_client.get_courses(search=function_args.get("search"), token=user_token)
                elif function_name == "get_course_details":
                    function_response = await lms_client.get_chatbot_course_details(course_id=function_args.get("course_id"), token=user_token)
                elif function_name == "get_assessments":
                    function_response = await lms_client.get_assessments(course_id=function_args.get("course_id"), token=user_token)
                elif function_name == "get_my_certificates":
                    function_response = await lms_client.get_my_certificates(token=user_token)
                elif function_name == "get_overall_stats":
                    function_response = await lms_client.get_overall_stats(token=user_token)
                elif function_name == "get_per_course_stats":
                    function_response = await lms_client.get_per_course_stats(token=user_token)
                elif function_name == "get_monthly_enrollments":
                    function_response = await lms_client.get_monthly_enrollments(months=function_args.get("months", 6), token=user_token)
                elif function_name == "get_course_faqs":
                    function_response = await lms_client.get_course_faqs(course_id=function_args.get("course_id"), token=user_token)
                elif function_name == "get_course_glossary":
                    function_response = await lms_client.get_course_glossary(course_id=function_args.get("course_id"), token=user_token)
                elif function_name == "get_course_sops":
                    function_response = await lms_client.get_course_sops(course_id=function_args.get("course_id"), token=user_token)
                elif function_name == "get_course_materials":
                    function_response = await lms_client.get_course_materials(course_id=function_args.get("course_id"), token=user_token)
                else:
                    function_response = {"error": "Function not found"}

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response),
                })
            
            # Second call to get the final answer after tool responses
            logger.info("Calling OpenAI (second call) for final response")
            try:
                second_response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.0
                )
                return second_response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI completion error (second call): {str(e)}")
                raise

        return response_message.content

def get_openai_service():
    return OpenAIService()
