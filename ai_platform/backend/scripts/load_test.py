import asyncio
import httpx
import time
import json

API_URL = "http://localhost:8000/api/v1"
CONCURRENT_USERS = 50

# A simple valid C++ program
CPP_CODE = """
#include <iostream>
using namespace std;
int main() {
    int n;
    if (cin >> n) {
        // Mock fib logic
        cout << 5 << endl;
    }
    return 0;
}
"""

async def simulate_user(client: httpx.AsyncClient, user_id: int):
    print(f"User {user_id} starting...")
    start_time = time.time()
    
    # 1. Register User & Login (Or just mock auth bypass if set up)
    username = f"loadtest_user_{user_id}_{int(start_time)}"
    
    try:
        reg_res = await client.post(
            f"{API_URL}/auth/register", 
            json={"username": username, "email": f"{username}@test.com", "password": "password123"}
        )
        if reg_res.status_code != 201:
            print(f"User {user_id} Failed to register: {reg_res.text}")
            return
            
        login_data = {"username": username, "password": "password123"}
        login_res = await client.post(f"{API_URL}/auth/login", data=login_data)
        
        token = login_res.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Submit Code
        submit_payload = {
            "problem_id": 1,
            "code": CPP_CODE,
            "language": "cpp"
        }
        
        submit_res = await client.post(f"{API_URL}/submit", json=submit_payload, headers=headers)
        if submit_res.status_code == 429: # Rate limit hit expected possibly
            print(f"User {user_id} Rate limited.")
            return
            
        task_id = submit_res.json()["task_id"]
        
        # 3. Poll for result
        while True:
            await asyncio.sleep(1.0)
            status_res = await client.get(f"{API_URL}/attempts/{task_id}")
            data = status_res.json()
            if data["status"] not in ["Pending", "Processing"]:
                duration = time.time() - start_time
                print(f"User {user_id} finished in {duration:.2f}s with status: {data['status']}")
                break
                
    except Exception as e:
        print(f"User {user_id} encountered an error: {e}")


async def main():
    print(f"Starting Load Test with {CONCURRENT_USERS} concurrent submissions...")
    async with httpx.AsyncClient() as client:
        tasks = [simulate_user(client, i) for i in range(CONCURRENT_USERS)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
