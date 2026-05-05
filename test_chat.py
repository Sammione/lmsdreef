import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_chat(prompt, token=None):
    url = "http://localhost:8000/api/chat/"
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}" if not token.startswith("Bearer ") else token
        print(f"Using Auth Token: {token[:10]}...")
    
    print(f"\n--- Testing Prompt: '{prompt}' ---")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                print("SUCCESS")
                print("Response:", response.json().get("response"))
            else:
                print(f"Error {response.status_code}:", response.text)
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Tip: Make sure your FastAPI server is running (uvicorn app.main:app --reload)")

async def main():
    # Token is now loaded from .env automatically
    test_token = os.getenv("LMS_API_KEY")
    
    # Test: Specific course info
    await test_chat("tell me everythng about this course Isolated Mini-Grid Project Development Process", token=test_token)

if __name__ == "__main__":
    asyncio.run(main())
