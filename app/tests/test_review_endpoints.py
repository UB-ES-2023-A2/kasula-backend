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
    
def delete_created_review(recipe_id, review_id, access_token, client):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = client.delete(f"/review/{recipe_id}/{review_id}", headers=headers)

    if response.status_code != 200:
        raise TestAssertionError(response=response)
    
def create_users_recipes_reviews(client):
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
    
    created_recipe_id = response.json()["_id"]

    # Create another user to add a review
    user2 = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "testpassword"
    }

    response_user2 = client.post("/user/", json=user2)
    response_token2 = client.post("/user/token", data={"username": "testuser2", "password": "testpassword"})

    if (response_user2.status_code != 201 or
        response_user2.json()["username"] != "testuser2" or
        response_user2.json()["email"] != "testuser2@example.com" or
        not is_valid_uuid(response_user2.json()["_id"])):
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        raise TestAssertionError(response=response_user2)
    
    access_token2 = response_token2.json()["access_token"]

    user_id2 = response_user2.json()["_id"]

    headers2 = {
        "Authorization": f"Bearer {access_token2}"
    }

    # Test creating a new review
    review = {
        "rating": 5,
        "comment": "This is a great recipe!"
    }

    data = {
        "review": (None, json.dumps(review), "application/json"),
    }

    response = client.post(f"/review/{created_recipe_id}", files=data, headers=headers2)

    if response.status_code != 201:
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        delete_created_user(user_id2, access_token2, client)
        raise TestAssertionError(response=response)
    
    created_review_id = response.json()["_id"]

    return user_id, access_token, created_recipe_id, user_id2, access_token2, created_review_id

def cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client):
    delete_created_review(created_recipe_id, created_review_id, access_token2, client)
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)
    delete_created_user(user_id2, access_token2, client)

def test_create_review(client):
    user_id, access_token, created_recipe_id, user_id2, access_token2, created_review_id = create_users_recipes_reviews(client)

    # Cleanup
    cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client)

def test_update_review(client):
    user_id, access_token, created_recipe_id, user_id2, access_token2, created_review_id = create_users_recipes_reviews(client)

    headers = {
        "Authorization": f"Bearer {access_token2}"
    }

    # Update the created review
    updated_review_data = {
        "rating": 4,
        "comment": "This is a great recipe! I love it!"
    }

    response_update = client.put(f"/review/{created_recipe_id}/{created_review_id}", json=updated_review_data, headers=headers)

    if (response_update.status_code != 200
        or response_update.json()["rating"] != 4.0
        or response_update.json()["comment"] != "This is a great recipe! I love it!"):
        cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client)
        raise TestAssertionError(response=response_update)
    
    # Cleanup
    cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client)

def test_delete_review(client):
    user_id, access_token, created_recipe_id, user_id2, access_token2, created_review_id = create_users_recipes_reviews(client)

    headers = {
        "Authorization": f"Bearer {access_token2}"
    }

    response_delete = client.delete(f"/review/{created_recipe_id}/{created_review_id}", headers=headers)

    if (response_delete.status_code != 200
        or response_delete.json()["message"] != "Review deleted successfully"):
        delete_created_recipe(created_recipe_id, access_token, client)
        delete_created_user(user_id, access_token, client)
        delete_created_user(user_id2, access_token2, client)
        raise TestAssertionError(response=response_delete)

    # Cleanup
    delete_created_recipe(created_recipe_id, access_token, client)
    delete_created_user(user_id, access_token, client)
    delete_created_user(user_id2, access_token2, client)

def test_get_reviews(client):
    user_id, access_token, created_recipe_id, user_id2, access_token2, created_review_id = create_users_recipes_reviews(client)

    # Test getting all reviews for a recipe
    response = client.get(f"/review/{created_recipe_id}")

    if response.status_code != 200 or response.json()[0]["_id"] != created_review_id:
        cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client)
        raise TestAssertionError(response=response)

    # Cleanup
    cleanup(created_recipe_id, created_review_id, user_id, access_token, user_id2, access_token2, client)