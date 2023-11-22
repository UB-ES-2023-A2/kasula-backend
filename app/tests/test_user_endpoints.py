import uuid
import json

# To test these endpoints, we will focus on the following testing parameters:

# 1. Happy Path: Testing when everything goes as expected.

# 2. Boundary/Edge Cases: Testing with the extremes.

# 3. Error Cases: Testing where we expect errors or failures.

class TestAssertionError(AssertionError):
    def __init__(self, response=None, message=''):
        super().__init__(message)
        self.response = response

@staticmethod
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def delete_created_user(user_id, access_token, client):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = client.delete(f"/user/{user_id}", headers=headers)

    if response.status_code != 200:
        raise TestAssertionError(response=response)

def test_create_user(client):
    # Test creating a new user
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response_original = client.post("/user/", json=user)

    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]        

    if (response_original.status_code != 201 or 
        response_original.json()["username"] != "testuser" or 
        response_original.json()["email"] != "testuser@example.com" or 
        not is_valid_uuid(response_original.json()["_id"])):
        delete_created_user(response_original.json()["_id"], access_token, client)
        raise TestAssertionError(response=response_original)

    # Test creating a user with an existing username
    response = client.post("/user/", json=user)

    if response.status_code != 400 or response.json()["detail"] != "Username or email already registered":
        delete_created_user(response.json()["_id"], access_token, client)
        raise TestAssertionError(response=response)

    # Test creating a user with an existing email
    user["username"] = "testuser2"
    response = client.post("/user/", json=user)

    if response.status_code != 400 or response.json()["detail"] != "Username or email already registered":
        delete_created_user(response.json()["_id"], access_token, client)
        raise TestAssertionError(response=response)

    # Test creating a user with an invalid email
    user["username"] = "testuser3"
    user["email"] = "testuser3"
    response = client.post("/user/", json=user)

    if response.status_code != 400 or response.json()["detail"] != "Invalid email format":
        delete_created_user(response.json()["_id"], access_token, client)
        raise TestAssertionError(response=response)

    # Delete the created user
    delete_created_user(response_original.json()["_id"], access_token, client)

def test_list_users(client):
    # Test listing all users
    response = client.get("/user/")

    if response.status_code != 200 or not isinstance(response.json(), list):
        raise TestAssertionError(response=response)

def test_get_me(client):
    # Create user for this test
    user = {
        "username": "getme_test",
        "email": "getme_test@example.com",
        "password": "getme_testpassword"
    }
    response_original = client.post("/user/", json=user)

    response_token = client.post("/user/token", data={"username": "getme_test", "password": "getme_testpassword"})
    access_token = response_token.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = client.get("/user/me", headers=headers)

    if (response.status_code != 200 or 
        response.json()["username"] != "getme_test"):
        delete_created_user(response_original.json()["_id"], access_token, client)
        raise TestAssertionError(response=response)

    # Delete the created user
    delete_created_user(response_original.json()["_id"], access_token, client)

def test_show_user(client):
    # Create user for this test
    user = {
        "username": "showuser_test",
        "email": "showuser_test@example.com",
        "password": "showuser_testpassword"
    }
    response = client.post("/user/", json=user)

    response_token = client.post("/user/token", data={"username": "showuser_test", "password": "showuser_testpassword"})
    access_token = response_token.json()["access_token"]

    user_id = response.json()["_id"]

    # Test fetching the created user
    response = client.get(f"/user/{user_id}")

    if (response.status_code != 200 or 
        response.json()["_id"] != user_id):
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Test fetching a user with an invalid id
    response = client.get("/user/123")

    if response.status_code != 404 or response.json()["detail"] != "User 123 not found":
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Delete the created user
    delete_created_user(user_id, access_token, client)

def test_update_user(client):
    # Create user for this test
    user = {
        "username": "updateuser_test",
        "email": "updateuser_test@example.com",
        "password": "updateuser_testpassword"
    }
    response_creation = client.post("/user/", json=user)

    response_token = client.post("/user/token", data={"username": "updateuser_test", "password": "updateuser_testpassword"})
    access_token = response_token.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_id = response_creation.json()["_id"]
    update_data = {
        "username": "updated_testuser"
    }

    # Test updating the created user
    response = client.put(f"/user/{user_id}", files={"user": (None, json.dumps(update_data), "application/json")}, headers=headers)

    if (response.status_code != 200 or 
        response.json()["username"] != "updated_testuser"):
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Delete the created user
    response_token = client.post("/user/token", data={"username": "updated_testuser", "password": "updateuser_testpassword"})
    access_token = response_token.json()["access_token"]
    delete_created_user(user_id, access_token, client)

def test_delete_user(client):
    # Create user for this test
    user = {
        "username": "deleteuser_test",
        "email": "deleteuser_test@example.com",
        "password": "deleteuser_testpassword"
    }
    response_creation = client.post("/user/", json=user)

    response_token = client.post("/user/token", data={"username": "deleteuser_test", "password": "deleteuser_testpassword"})
    access_token = response_token.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_id = response_creation.json()["_id"]

    # Test deleting the created user
    response = client.delete(f"/user/{user_id}", headers=headers)

    if (response.status_code != 200 or 
        response.json()["message"] != "User successfully deleted"):
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

def test_login_for_access_token(client):
    # Create user for this test
    user = {
        "username": "token_test",
        "email": "token_test@example.com",
        "password": "token_testpassword"
    }
    response_create = client.post("/user/", json=user)

    response_original = client.post("/user/token", data={"username": "token_test", "password": "token_testpassword"})

    if (response_original.status_code != 200 or 
        "access_token" not in response_original.json()):
        raise TestAssertionError(response=response_original)

    # Test logging in with invalid credentials
    response = client.post("/user/token", data={"username": "token_test", "password": "wrongpassword"})

    if (response.status_code != 401 or 
        response.json()["detail"] != "Incorrect username or password"):
        raise TestAssertionError(response=response)
    
    # Delete the created user
    delete_created_user(response_create.json()["_id"], response_original.json()["access_token"], client)

def test_follow_user(client):
    # Create user for this test
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response_create = client.post("/user/", json=user)

    response_original = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})

    if (response_original.status_code != 200 or
        "access_token" not in response_original.json()):
        raise TestAssertionError(response=response_original)
    
    access_token = response_original.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Create another user to follow
    user2 = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "testpassword"
    }
    response_create2 = client.post("/user/", json=user2)

    response_original2 = client.post("/user/token", data={"username": "testuser2", "password": "testpassword"})

    access_token2 = response_original2.json()["access_token"]

    # Test following a user
    response = client.post("/user/follow/testuser2", headers=headers)

    if (response.status_code != 200 or
        response.json()["message"] != "Now following user testuser2"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Test following a user that doesn't exist
    response = client.post("/user/follow/testuser3", headers=headers)

    if (response.status_code != 404 or
        response.json()["detail"] != "User testuser3 not found"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Test following a user that is already followed
    response = client.post("/user/follow/testuser2", headers=headers)

    if (response.status_code != 400 or
        response.json()["detail"] != "You are already following user testuser2"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Delete the created users
    delete_created_user(response_create.json()["_id"], access_token, client)
    delete_created_user(response_create2.json()["_id"], access_token2, client)

def test_unfollow_user(client):
    # Create user for this test
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response_create = client.post("/user/", json=user)

    response_original = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})

    if (response_original.status_code != 200 or
        "access_token" not in response_original.json()):
        raise TestAssertionError(response=response_original)
    
    access_token = response_original.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Create another user to follow
    user2 = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "testpassword"
    }
    response_create2 = client.post("/user/", json=user2)

    response_original2 = client.post("/user/token", data={"username": "testuser2", "password": "testpassword"})

    access_token2 = response_original2.json()["access_token"]

    # Test following a user
    response = client.post("/user/follow/testuser2", headers=headers)

    if (response.status_code != 200 or
        response.json()["message"] != "Now following user testuser2"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Test unfollowing a user
    response = client.post("/user/unfollow/testuser2", headers=headers)

    if (response.status_code != 200 or
        response.json()["message"] != "Unfollowed user testuser2"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Test unfollowing a user that doesn't exist
    response = client.post("/user/unfollow/testuser3", headers=headers)

    if (response.status_code != 404 or
        response.json()["detail"] != "User testuser3 not found"):
        delete_created_user(response_create.json()["_id"], access_token, client)
        delete_created_user(response_create2.json()["_id"], access_token2, client)
        raise TestAssertionError(response=response)
    
    # Delete the created users
    delete_created_user(response_create.json()["_id"], access_token, client)
    delete_created_user(response_create2.json()["_id"], access_token2, client)



