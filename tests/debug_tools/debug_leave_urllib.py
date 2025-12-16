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


BASE_URL = "http://localhost:8000"

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
            # Login uses form data
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
        join_user = get_random_user()
        password = "password123"

        print(f"1. Setup Organizer ({org_user})")
        # Register Org
        s, r = request_api("POST", "/users/", {"username": org_user, "password": password})
        print(f"Register Status: {s}, Response: {r}")
        
        # Login Org
        s, r = request_api("POST", "/auth/login", {"username": org_user, "password": password}, is_form=True)
        if s != 200:
            print(f"Login Org Failed: {s} {r}")
            sys.exit(1)
        org_token = r["access_token"]
        print("Org Logged in.")

        print("2. Create Ride")
        s, ride = request_api("POST", "/rides/", {
            "title": "Debug Ride",
            "description": "Test leave",
            "start_time": "2025-12-10T10:00:00"
        }, token=org_token)
        if s != 201:
             print(f"Create Ride Failed: {s} {ride}")
             sys.exit(1)
        print(f"Ride created: {ride['id']} Code: {ride['code']}")

        print(f"3. Setup Joiner ({join_user})")
        # Register Joiner
        s, r = request_api("POST", "/users/", {"username": join_user, "password": password})
        
        # Login Joiner
        s, r = request_api("POST", "/auth/login", {"username": join_user, "password": password}, is_form=True)
        if s != 200:
            print(f"Login Joiner Failed: {s} {r}")
            sys.exit(1)
        join_token = r["access_token"]
        print("Joiner Logged in.")

        print("4. Join Ride")
        s, r = request_api("POST", "/participations/", {"ride_code": ride['code']}, token=join_token)
        if s == 201:
            part_id = r["id"]
        elif s == 409:
            print("Already joined, getting ID...")
            # Fetch all and find
            s, parts = request_api("GET", "/participations/", token=join_token)
            part_id = None
            for p in parts:
                if p["ride_id"] == ride['id']:
                    part_id = p["id"]
                    break
        else:
            print(f"Join Ride Failed: {s} {r}")
            sys.exit(1)
            
        print(f"Participation ID: {part_id}")
        if not part_id:
            print("Could not find participation ID")
            sys.exit(1)

        print(f"5. Leave Ride (Participation ID: {part_id})")
        s, r = request_api("DELETE", f"/participations/{part_id}", token=join_token)
        if s == 204:
            print("Left ride successfully (204).")
        else:
            print(f"Leave Ride Failed: {s} {r}")
            sys.exit(1)

        print("6. Verify Deletion")
        s, r = request_api("GET", f"/participations/{part_id}", token=join_token)
        if s == 404:
            print("SUCCESS: Participation verified as deleted (404).")
        else:
            print(f"FAILURE: Participation still exists? Status: {s}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
