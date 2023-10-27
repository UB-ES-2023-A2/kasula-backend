import json
from bson import ObjectId
from fastapi.testclient import TestClient
import sys
from app.main import app

# To test these endpoints, we will focus on the following testing parameters:

# 1. Happy Path: Testing when everything goes as expected.

# 2. Boundary/Edge Cases: Testing with the extremes.

# 3. Error Cases: Testing where we expect errors or failures.

client = TestClient(app)

def test_hello_world():
    # Test the root path
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_create_user():
    # Test creating a new user
    user = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response = client.post("/users/", json=user)
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "testuser@example.com"
    assert isinstance(ObjectId(response.json()["_id"]), ObjectId)

    # Test creating a user with an existing username
    response = client.post("/users/", json=user)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already registered"

def test_list_users():
    # Test listing all users
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

