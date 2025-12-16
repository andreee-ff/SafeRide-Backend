import requests
import sys

BASE_URL = "http://localhost:8000"

def register_user(username, password):
    resp = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
    if resp.status_code == 201:
        return resp.json()
    if resp.status_code == 409:
        print(f"User {username} already exists, login instead.")
        return None
    raise Exception(f"Failed to register: {resp.text}")

def login_user(username, password):
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    raise Exception(f"Failed to login: {resp.text}")

def create_ride(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": "Debug Ride",
        "description": "Test leave",
        "start_time": "2025-12-10T10:00:00"
    }
    resp = requests.post(f"{BASE_URL}/rides/", json=data, headers=headers)
    if resp.status_code != 201:
        raise Exception(f"Failed to create ride: {resp.text}")
    return resp.json()

def join_ride(token, ride_code):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/participations/", json={"ride_code": ride_code}, headers=headers)
    if resp.status_code == 409:
        print("Already joined.")
        # We need to find the participation ID.
        # This part is tricky if we don't return it on 409.
        # But for clean test, we assume fresh join.
        pass
    elif resp.status_code != 201:
        raise Exception(f"Failed to join: {resp.text}")
    
    # We need the participation ID.
    # On 201, it returns ParticipationResponse
    if resp.status_code == 201:
        return resp.json()["id"]
    return None

def get_my_participations(token, ride_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/participations/", headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to get participations: {resp.text}")
    parts = resp.json()
    # Find the one for ride_id
    # Note: /participations/ returns ALL, we need to filter by user on client side in script?
    # Wait, the endpoint returns ALL participations for EVERYONE?
    # Yes, we saw that suspicious code earlier.
    # But User B only cares about their own participation ID for this ride.
    # Participation objects have user_id. We need to know User B's user_id.
    # Or just search where ride_id matches and hope we find the right one?
    # Actually, we received the ID on join.
    # If we fall back here, we search for ride_id.
    for p in parts:
        if p["ride_id"] == ride_id:
            return p["id"]
    return None

def leave_ride(token, participation_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.delete(f"{BASE_URL}/participations/{participation_id}", headers=headers)
    if resp.status_code != 204:
        raise Exception(f"Failed to leave: {resp.text}")
    print("Left ride successfully (204).")

def main():
    try:
        # 1. Setup Organizer
        try:
            register_user("org_user", "password")
        except:
            pass # ignore
        org_token = login_user("org_user", "password")
        
        # 2. Create Ride
        ride = create_ride(org_token)
        print(f"Ride created: {ride['id']} Code: {ride['code']}")

        # 3. Setup Joiner
        try:
            register_user("join_user", "password")
        except:
             pass
        join_token = login_user("join_user", "password")

        # 4. Join Ride
        print("Joining ride...")
        part_id = join_ride(join_token, ride['code'])
        
        if not part_id:
            # Maybe already joined, find ID
            print("Finding participation ID...")
            part_id = get_my_participations(join_token, ride['id'])
        
        print(f"Participation ID: {part_id}")

        if not part_id:
            print("FAILED: Could not find participation ID")
            sys.exit(1)

        # 5. Leave Ride
        print(f"Leaving ride (Participation ID: {part_id})...")
        leave_ride(join_token, part_id)

        # 6. Verify
        # Try to find participation again
        check_id = get_my_participations(join_token, ride['id'])
        if check_id and check_id == part_id:
             # Wait, get_my_participations logic in script returns ANY participation with ride_id.
             # We should verify that THIS specific participation ID is gone.
             # Or better, check /participants/id returns 404
             headers = {"Authorization": f"Bearer {join_token}"}
             resp = requests.get(f"{BASE_URL}/participations/{part_id}", headers=headers)
             if resp.status_code == 404:
                 print("SUCCESS: Participation not found (verified deleted).")
             else:
                 print(f"FAILURE: Participation still exists? Status: {resp.status_code}")
                 sys.exit(1)
        else:
             print("SUCCESS: Participation not found in list.")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
