import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import settings
from app_definition import app

# Import the test functions
import test_user_endpoints as test_user_endpoints
from test_user_endpoints import TestAssertionError

def initialize():
    # Connect to the MongoDB database
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]

    print("\nConnected to the test database.\n")

def run_single_test(test_func):
    try:
        test_func()
        result = (test_func.__name__, "PASSED✅")
    except TestAssertionError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()["detail"]
        except:
            pass
        result = (test_func.__name__, f"FAILED👎🏻. {str(e)} Detail: {error_detail}")
    except AssertionError as e:  # Catch general assertion errors if any
        result = (test_func.__name__, f"FAILED👎🏻. {e}")

    # Print the result immediately after running the test
    print(f"{result[0]} - {result[1]}")

    return result

def cleanup():
    # Disconnect from the MongoDB database
    app.mongodb_client.close()

    print("\nDisconnected from the test database.\n")

def run_tests():
    initialize()
    
    user_test_functions = [
        test_user_endpoints.test_create_user,
        test_user_endpoints.test_list_users,
        test_user_endpoints.test_get_me,
        test_user_endpoints.test_show_user,
        test_user_endpoints.test_update_user,
        test_user_endpoints.test_delete_user,
        test_user_endpoints.test_login_for_access_token,
        # Add more tests as needed
    ]

    results = [run_single_test(test_func) for test_func in user_test_functions]
    
    cleanup()

if __name__ == "__main__":
    run_tests()
