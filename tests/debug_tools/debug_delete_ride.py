import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import random
import time

BASE_URL = "http://localhost:8000"

def get_random_user():
    suffix = int(time.time())
    return f"user_{suffix}_{random.randint(1000,9999)}"

def request_api(method, endpoint, data=None, token=None, is_form=False):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if not is_form:
        headers["Content-Type"] = "application/json"
    else:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = None
    if data:
        if is_form:
             encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        else:
            encoded_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read()
            if body:
                return status, json.loads(body)
            return status, None
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read()
        try:
             json_body = json.loads(body) if body else None
             return status, json_body
        except:
             print(f"FAILED JSON DECODE: {body}")
             return status, body

def main():
    try:
        org_user = get_random_user()
        password = "password123"

        print(f"1. Setup Organizer ({org_user})")
        # Register Org
        s, r = request_api("POST", "/users/", {"username": org_user, "password": password})
        if s != 201:
             print(f"Register Organizer Failed: {s} {r}")
             sys.exit(1)
        
        # Login Org
        s, r = request_api("POST", "/auth/login", {"username": org_user, "password": password}, is_form=True)
        if s != 200:
            print(f"Login Org Failed: {s} {r}")
            sys.exit(1)
        org_token = r["access_token"]
        print("Org Logged in.")

        print("2. Create Ride")
        s, ride = request_api("POST", "/rides/", {
            "title": "Debug Ride Delete",
            "description": "Test delete",
            "start_time": "2025-12-10T10:00:00"
        }, token=org_token)
        if s != 201:
             print(f"Create Ride Failed: {s} {ride}")
             sys.exit(1)
        ride_id = ride['id']
        print(f"Ride created: {ride_id}")

        print("3. Check Participants (Auto-join check)")
        s, parts = request_api("GET", f"/rides/{ride_id}/participants", token=org_token)
        if s == 200:
            print(f"Participants count: {len(parts)}")
            if len(parts) == 0:
                print("WARNING: Creator not auto-added?")
        else:
             print(f"Check Participants Failed: {s} {parts}")

        print(f"4. Delete Ride ({ride_id})")
        s, r = request_api("DELETE", f"/rides/{ride_id}", token=org_token)
        if s == 204:
            print("Delete ride successfully (204).")
        else:
            print(f"Delete Ride Failed: {s} {r}")
            sys.exit(1)

        print("5. Verify Deletion (Get by ID)")
        s, r = request_api("GET", f"/rides/{ride_id}", token=org_token)
        if s == 404:
            print("SUCCESS: Ride verified as deleted (404).")
        else:
            print(f"FAILURE: Ride still exists? Status: {s}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
