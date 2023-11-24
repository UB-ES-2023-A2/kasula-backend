import json
import uuid

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

def delete_created_recipe(recipe_id: str, token: str, client):
    """Helper function to delete a created recipe during testing."""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = client.delete(f"/recipe/{recipe_id}", headers=headers)

    if response.status_code != 200:
        raise TestAssertionError(response=response)

def delete_created_user(user_id, access_token, client):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = client.delete(f"/user/{user_id}", headers=headers)

    if response.status_code != 200:
        raise TestAssertionError(response=response)

def test_create_recipe(client):
    # Authenticate the user first
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }

    response_user = client.post("/user/", json=user)
    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]

    if (response_user.status_code != 201 or 
        response_user.json()["username"] != "testuser" or 
        response_user.json()["email"] != "testuser@example.com" or 
        not is_valid_uuid(response_user.json()["_id"])):
        raise TestAssertionError(response=response_user)

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Test creating a new recipe
    recipe = {
        "name": "Glass of Water",
        "ingredients": [
            {
                "name": "Water",
                "quantity": 1,
                "unit": "cup"
            }
        ],
        "instructions": [
            {
                "body": "Get a cup",
                "step_number": 0
            },
            {
            "body": "Pour Water",
            "step_number": 1
            }
        ],
        "cooking_time": 1,
        "difficulty": 0
    }

    data = {
        "recipe": (None, json.dumps(recipe), "application/json"),
    }
    response = client.post("/recipe/", files=data, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Cleanup
    created_recipe_id = response.json()["_id"]
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_list_recipes(client):
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }

    response_user = client.post("/user/", json=user)
    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Test listing all recipes
    response = client.get("/recipe/", headers=headers)

    if response.status_code != 200:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    delete_created_user(user_id, access_token, client)

def test_show_recipe(client):
    # Authenticate and create a test recipe
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }

    response_user = client.post("/user/", json=user)
    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    recipe = {
        "name": "Glass of Water",
        "ingredients": [
            {
                "name": "Water",
                "quantity": 1,
                "unit": "cup"
            }
        ],
        "instructions": [
            {
                "body": "Get a cup",
                "step_number": 0
            },
            {
            "body": "Pour Water",
            "step_number": 1
            }
        ],
        "cooking_time": 1,
        "difficulty": 0,
        "image": "None"
    }
    response_original = client.post("/recipe/", files={"recipe": (None, json.dumps(recipe), "application/json")}, headers=headers)
    created_recipe_id = response_original.json()["_id"]

    # Test getting a single recipe by ID
    response = client.get(f"/recipe/{created_recipe_id}", headers=headers)

    if response.status_code != 200 or response.json()["_id"] != created_recipe_id:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Test getting a non-existing recipe by ID
    response = client.get("/recipe/1234", headers=headers)

    if response.status_code != 404:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_update_recipe(client):
    # Authenticate the user first (This is the same as the previous test)
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response_user = client.post("/user/", json=user)
    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    recipe = {
        "name": "Glass of Water",
        "ingredients": [
            {
                "name": "Water",
                "quantity": 1,
                "unit": "cup"
            }
        ],
        "instructions": [
            {
                "body": "Get a cup",
                "step_number": 0
            },
            {
            "body": "Pour Water",
            "step_number": 1
            }
        ],
        "cooking_time": 1,
        "difficulty": 0,
        "image": "None"
    }
    
    response = client.post("/recipe/", files={"recipe": (None, json.dumps(recipe), "application/json")}, headers=headers)
    created_recipe_id = response.json()["_id"]

    # Update the created recipe
    updated_recipe_data = {
        "name": "Glass of Cold Water",
        "cooking_time": 2
    }
    
    response_update = client.put(f"/recipe/{created_recipe_id}", files={"recipe": (None, json.dumps(updated_recipe_data), "application/json")}, headers=headers)

    if (response_update.status_code != 200
        or response_update.json()["name"] != "Glass of Cold Water"
        or response_update.json()["cooking_time"] != 2):
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_update)

    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_delete_recipe(client):
    # Authenticate the user first (This is the same as the previous test)
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response_user = client.post("/user/", json=user)
    response_token = client.post("/user/token", data={"username": "testuser", "password": "testpassword"})
    access_token = response_token.json()["access_token"]

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    recipe = {
        "name": "Glass of Water",
        "ingredients": [
            {
                "name": "Water",
                "quantity": 1,
                "unit": "cup"
            }
        ],
        "instructions": [
            {
                "body": "Get a cup",
                "step_number": 0
            },
            {
            "body": "Pour Water",
            "step_number": 1
            }
        ],
        "cooking_time": 1,
        "difficulty": 0,
        "image": "None"
    }
    response = client.post("/recipe/", files={"recipe": (None, json.dumps(recipe), "application/json")}, headers=headers)
    created_recipe_id = response.json()["_id"]

    # Delete the created recipe
    response_delete = client.delete(f"/recipe/{created_recipe_id}", headers=headers)

    if (response_delete.status_code != 200
        or response_delete.json()["message"] != "Recipe successfully deleted"):
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_delete)

    # Cleanup
    delete_created_user(user_id, access_token, client)