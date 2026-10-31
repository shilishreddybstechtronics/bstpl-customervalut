import sys
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from main import app
from auth import create_token, hash_password
import models
from database import SessionLocal

client = TestClient(app)

def test_endpoints():
    db = SessionLocal()
    # Find or use an existing user to create a real token
    user = db.query(models.User).filter(models.User.user_id == "0001").first()
    if not user:
        # Create a mock test user in memory or find first user
        user = db.query(models.User).first()
    
    assert user is not None, "At least one user must exist in the database"
    token = create_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing with user: {user.name} ({user.user_id})")

    # 1. Test /auth/me
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200, f"/auth/me returned {res.status_code}: {res.text}"
    data = res.json()
    assert "name" in data
    assert "previous_name" in data
    assert "theme_palette" in data
    assert "theme_mode" in data
    print("✓ /auth/me returned valid profile with previous_name and theme preferences.")

    # 2. Test /api/me/name
    orig_name = user.name
    temp_name = orig_name + " Test"
    
    # Try with wrong confirm
    res = client.put("/api/me/name", json={"name": temp_name, "confirm_current_name": "Wrong Name"}, headers=headers)
    assert res.status_code == 400, "Should reject wrong current name"
    
    # Try with same name
    res = client.put("/api/me/name", json={"name": orig_name, "confirm_current_name": orig_name}, headers=headers)
    assert res.status_code == 400, "Should reject identical name"

    # Valid name update
    res = client.put("/api/me/name", json={"name": temp_name, "confirm_current_name": orig_name}, headers=headers)
    assert res.status_code == 200, f"/api/me/name returned {res.status_code}: {res.text}"
    assert res.json()["name"] == temp_name
    assert res.json()["previous_name"] == orig_name

    # Restore original name
    res = client.put("/api/me/name", json={"name": orig_name, "confirm_current_name": temp_name}, headers=headers)
    assert res.status_code == 200
    print("✓ /api/me/name validated and updated successfully.")

    # 3. Test /api/me/theme
    res = client.put("/api/me/theme", json={"palette": "sunset", "mode": "dark"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["palette"] == "sunset"
    assert res.json()["mode"] == "dark"

    res = client.get("/api/me/theme", headers=headers)
    assert res.status_code == 200
    assert res.json()["palette"] == "sunset"
    assert res.json()["mode"] == "dark"

    # Reset to default royal_navy light
    client.put("/api/me/theme", json={"palette": "royal_navy", "mode": "light"}, headers=headers)
    print("✓ /api/me/theme persisted and retrieved successfully.")

    # 4. Test /api/users
    res = client.get("/api/users", headers=headers)
    assert res.status_code == 200
    users_list = res.json()
    assert isinstance(users_list, list)
    print(f"✓ /api/users returned {len(users_list)} users.")

    # 5. Test /api/activity
    res = client.get("/api/activity?page=1&page_size=5", headers=headers)
    assert res.status_code == 200
    act_data = res.json()
    assert "items" in act_data
    print(f"✓ /api/activity returned {len(act_data['items'])} audit log entries.")

    # 6. Test /auth/logout
    res = client.post("/auth/logout", headers=headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    print("✓ /auth/logout completed successfully.")

    db.close()
    print("\nALL BACKEND API ENDPOINTS TESTED AND VERIFIED PERFECTLY!")

if __name__ == "__main__":
    test_endpoints()

