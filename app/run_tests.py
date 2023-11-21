import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.testclient import TestClient

from app.config import settings
from main import app

# Import the test functions
from tests import test_user_endpoints, test_recipe_endpoints
from tests.test_user_endpoints import TestAssertionError

async def clear_collections():
    await app.mongodb["users"].drop()
    await app.mongodb["recipes"].drop()


# Connect to the Database and clear the collections
def initialize():
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_TEST]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(clear_collections())
    app.mongodb_client.close()

    print("\nConnected to the test database and cleared collections.\n")

    return app

def run_single_test(test_func, client):
    try:
        test_func(client)
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

def run_tests():
    
    # Change the database for tests to not use the main database
    settings.DB_NAME = settings.DB_TEST

    app = initialize()
    
    user_test_functions = [
        test_user_endpoints.test_create_user,
        test_user_endpoints.test_list_users,
        test_user_endpoints.test_get_me,
        test_user_endpoints.test_show_user,
        test_user_endpoints.test_update_user,
        test_user_endpoints.test_delete_user,
        test_user_endpoints.test_login_for_access_token,
    ]

    recipe_test_functions = [
        test_recipe_endpoints.test_create_recipe,
        test_recipe_endpoints.test_list_recipes,
        test_recipe_endpoints.test_show_recipe,
        test_recipe_endpoints.test_update_recipe,
        test_recipe_endpoints.test_delete_recipe,
    ]

    # User tests
    # Make a print of the test name, around a line of dashes
    print("\n" + "=" * 40)
    print(" " * 12 + "USER TESTS" + " " * 12)
    print("=" * 40 + "\n")

    with TestClient(app) as client:
        [run_single_test(test_func, client) for test_func in user_test_functions]

        print("\n" + "-" * 50 + "\n")

        # Recipe tests
        print("\n" + "=" * 40)
        print(" " * 12 + "RECIPE TESTS" + " " * 12)
        print("=" * 40 + "\n")
        
        [run_single_test(test_func, client) for test_func in recipe_test_functions]
    
    # cleanup() # Maybe in the future we should only connect once to the Database
    # to fasten up the test execution but right now it is not a priority

if __name__ == "__main__":
    run_tests()
