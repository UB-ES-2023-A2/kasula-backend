from fastapi.testclient import TestClient
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.test_app import unit_tests
from app.config import settings

# Import the test functions
from tests import test_user_endpoints, test_recipe_endpoints
from tests.test_user_endpoints import TestAssertionError

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
    start = time.time()
    with TestClient(unit_tests) as client:
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
        print(" " * 12 + "USER UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in user_test_functions]

        print("\n" + "-" * 50 + "\n")

        # Recipe tests
        print("\n" + "=" * 40)
        print(" " * 12 + "RECIPE UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")
        
        [run_single_test(test_func, client) for test_func in recipe_test_functions]

    end = time.time()
    print(f"\nTotal time taken (Unit Tests): {end - start} seconds")

    settings.TEST_ENV = True
    from app.app_definition import app
    start = time.time()
    with TestClient(app) as client:
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
        print(" " * 8 + "USER INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in user_test_functions]

        print("\n" + "-" * 50 + "\n")

        # Recipe tests
        print("\n" + "=" * 40)
        print(" " * 8 + "RECIPE INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")
        
        [run_single_test(test_func, client) for test_func in recipe_test_functions]

    settings.TEST_ENV = False
    end = time.time()
    print(f"\nTotal time taken (Integration Tests): {end - start} seconds")


if __name__ == "__main__":
    run_tests()
