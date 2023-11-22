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
    
def delete_created_collection(collection_id, access_token, client):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = client.delete(f"/collection/{collection_id}", headers=headers)

    if response.status_code != 200:
        raise TestAssertionError(response=response)
    
def test_favorite_collection(client):
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

    # When creating a user, a default favorite collection is created
    response = client.get("/collection/user/testuser", headers=headers)

    if response.status_code != 200:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Check if the default favorite collection is created
    if (response.json()[0]["name"] != "Favorites" or
        response.json()[0]["description"] != "Here you can see your favorite recipes!" or
        response.json()[0]["recipe_ids"] != [] or
        response.json()[0]["user_id"] != user_id or
        response.json()[0]["username"] != "testuser" or
        response.json()[0]["favorite"] != True):
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Cleanup
    delete_created_user(user_id, access_token, client)

def test_create_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Cleanup
    created_collection_id = response.json()["_id"]
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_delete_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test deleting the created collection
    created_collection_id = response.json()["_id"]
    response_delete = client.delete(f"/collection/{created_collection_id}", headers=headers)

    if response_delete.status_code != 200:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_delete)
    
    # Cleanup
    delete_created_user(user_id, access_token, client)
        
def test_update_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test updating the created collection
    created_collection_id = response.json()["_id"]

    collection_update = {
        "name": "Updated Test Collection",
        "description": "This is an updated test collection"
    }

    response_update = client.put(f"/collection/{created_collection_id}", json=collection_update, headers=headers)

    if response_update.status_code != 200:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_update)
    
    # Cleanup
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_add_recipe_to_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test adding a recipe to the created collection
    created_collection_id = response.json()["_id"]

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
    
    created_recipe_id = response.json()["_id"]

    response_add = client.put(f"/collection/{created_collection_id}/add_recipe/{created_recipe_id}", headers=headers)

    if response_add.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_add)
    
    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_remove_recipe_from_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test adding a recipe to the created collection
    created_collection_id = response.json()["_id"]

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
    
    created_recipe_id = response.json()["_id"]

    response_add = client.put(f"/collection/{created_collection_id}/add_recipe/{created_recipe_id}", headers=headers)

    if response_add.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_add)
    
    # Test removing a recipe from the created collection
    response_remove = client.put(f"/collection/{created_collection_id}/remove_recipe/{created_recipe_id}", headers=headers)

    if response_remove.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_remove)
    
    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_list_collections_by_user(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)
    created_collection_id = response.json()["_id"]

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test listing all collections of a user
    response_list = client.get("/collection/user/testuser", headers=headers)

    # Check that response.status_code is 200 and that the response body is a list of 2 collections
    if response_list.status_code != 200 or len(response_list.json()) < 2:
        delete_created_collection(created_collection_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_list)
    
    # Cleanup
    created_collection_id = response.json()["_id"]
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_list_recipes_in_collection(client):
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

    # Test creating a new collection
    collection = {
        "name": "Test Collection",
        "description": "This is a test collection",
        "recipe_ids": []
    }

    response = client.post("/collection/", json=collection, headers=headers)

    if response.status_code != 201:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)
    
    # Test adding a recipe to the created collection
    created_collection_id = response.json()["_id"]

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
    
    created_recipe_id = response.json()["_id"]

    response_add = client.put(f"/collection/{created_collection_id}/add_recipe/{created_recipe_id}", headers=headers)

    if response_add.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_add)
    
    # Test listing all recipes in the created collection
    response_list = client.get(f"/collection/{created_collection_id}/recipes", headers=headers)

    # Check that response.status_code is 200 and that the response body is a list of 1 recipe
    if response_list.status_code != 200 or len(response_list.json()) != 1:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_list)
    
    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_collection(created_collection_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_get_favorites_collection(client):
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
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_user)

    user_id = response_user.json()["_id"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # When creating a user, a default favorite collection is created
    response = client.get("/collection/favorites/testuser", headers=headers)

    if response.status_code != 200:
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response)

    # Cleanup
    delete_created_user(user_id, access_token, client)

def test_add_recipe_favorite_collection(client):
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
    
    created_recipe_id = response.json()["_id"]

    response_add = client.patch(f"/collection/favorites/add_recipe/{created_recipe_id}/", headers=headers)

    if response_add.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_add)
    
    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)

def test_remove_recipe_favorite_collection(client):
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
    
    created_recipe_id = response.json()["_id"]

    response_add = client.patch(f"/collection/favorites/add_recipe/{created_recipe_id}/", headers=headers)

    if response_add.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_add)
    
    # Test removing a recipe from the created collection
    response_remove = client.patch(f"/collection/favorites/remove_recipe/{created_recipe_id}/", headers=headers)

    if response_remove.status_code != 200:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_remove)
    
    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)