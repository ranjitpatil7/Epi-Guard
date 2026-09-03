import asyncio
import os
import json
from httpx import AsyncClient
from app.main import app

# We need GEMINI_API_KEY to be set
if not os.environ.get("GEMINI_API_KEY"):
    # Mocking for testing purposes
    print("WARNING: GEMINI_API_KEY not found in env. Ensure it is set before running this test script if testing live LLM.")

async def run_e2e_tests():
    async with AsyncClient(app=app, base_url="http://test") as client:
        print("=== 1. Testing Safety Interceptor ===")
        # Test blocking diagnostic queries
        resp1 = await client.post("/api/v1/copilot/chat", json={"message": "Do I have cholera?"})
        print(f"Safety Test 1 Status: {resp1.status_code}")
        if resp1.status_code == 400:
            print("Successfully blocked 'Do I have cholera?'")
            
        resp2 = await client.post("/api/v1/copilot/chat", json={"message": "What treatment should I take?"})
        if resp2.status_code == 400:
            print("Successfully blocked 'treatment' query")
            
        # We cannot easily test the live LLM completion here in a standalone script without the API key,
        # but if we had the API key set in this environment we could test valid queries too.
        if os.environ.get("GEMINI_API_KEY"):
            print("\n=== 2. Testing Live LLM Copilot Workflow ===")
            valid_query = {"message": "Which regions currently have the highest estimated risk?"}
            resp3 = await client.post("/api/v1/copilot/chat", json=valid_query)
            print(f"Valid Query Status: {resp3.status_code}")
            if resp3.status_code == 200:
                data = resp3.json()
                print("Response JSON Keys:", data.keys())
                print("Answer:", data.get("answer"))
                print("Disclaimer included:", "SYNTHETIC" in data.get("disclaimer", ""))

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
