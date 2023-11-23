from fastapi.testclient import TestClient
import sys
import os
import time
import coverage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.test_app import unit_tests
from app.config import settings

# Import the test functions
from tests import test_user_endpoints, test_recipe_endpoints, test_review_endpoints
from tests import test_collection_endpoints, test_security_hashing, test_token
from tests.test_user_endpoints import TestAssertionError

def run_single_test(test_func, client, extra=False):
    try:
        if extra:
            test_func()
            result = (test_func.__name__, "PASSED✅")
        else:
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
    # Initialize the coverage object, omitting 'tests' and 'models' directories
    cov = coverage.Coverage(omit=['*/app/models/*', '*/app/run_tests.py'])
    cov.start()
    
    user_test_functions = [
            test_user_endpoints.test_create_user,
            test_user_endpoints.test_list_users,
            test_user_endpoints.test_get_me,
            test_user_endpoints.test_show_user,
            test_user_endpoints.test_update_user,
            test_user_endpoints.test_delete_user,
            test_user_endpoints.test_login_for_access_token,
            test_user_endpoints.test_follow_user,
            test_user_endpoints.test_unfollow_user,
    ]

    recipe_test_functions = [
        test_recipe_endpoints.test_create_recipe,
        test_recipe_endpoints.test_list_recipes,
        test_recipe_endpoints.test_show_recipe,
        test_recipe_endpoints.test_update_recipe,
        test_recipe_endpoints.test_delete_recipe,
    ]

    review_test_functions = [
        test_review_endpoints.test_create_review,
        test_review_endpoints.test_update_review,
        test_review_endpoints.test_delete_review,
        test_review_endpoints.test_get_reviews,
    ]

    collections_test_functions = [
        test_collection_endpoints.test_favorite_collection,
        test_collection_endpoints.test_create_collection,
        test_collection_endpoints.test_delete_collection,
        test_collection_endpoints.test_update_collection,
        test_collection_endpoints.test_add_recipe_to_collection,
        test_collection_endpoints.test_remove_recipe_from_collection,
        test_collection_endpoints.test_list_collections_by_user,
        test_collection_endpoints.test_list_recipes_in_collection,
        test_collection_endpoints.test_get_favorites_collection,
        test_collection_endpoints.test_add_recipe_favorite_collection,
        test_collection_endpoints.test_remove_recipe_favorite_collection,
    ]

    security_hashing_test_functions = [
        test_security_hashing.test_hash_password,
        test_security_hashing.test_verify_password,
    ]

    token_test_functions = [
        test_token.test_create_access_token_default_expires,
        test_token.test_create_access_token_custom_expires,
        test_token.test_create_access_token_with_additional_data,
    ]
    
    # Unit tests
    start = time.time()
    with TestClient(unit_tests) as client:
        # User testss
        print("\n" + "=" * 40)
        print(" " * 12 + "USER UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in user_test_functions]

    with TestClient(unit_tests) as client:
        # Recipe tests
        print("\n" + "=" * 40)
        print(" " * 12 + "RECIPE UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")
        
        [run_single_test(test_func, client) for test_func in recipe_test_functions]

    with TestClient(unit_tests) as client:
        # Review tests
        print("\n" + "=" * 40)
        print(" " * 12 + "REVIEW UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in review_test_functions]

    with TestClient(unit_tests) as client:
        # Collection tests
        print("\n" + "=" * 40)
        print(" " * 10 + "COLLECTION UNIT TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in collections_test_functions]

    end = time.time()
    print(f"\nTotal time taken (Unit Tests): {end - start} seconds")

    # Integration tests
    settings.TEST_ENV = True
    from app.app_definition import app
    start = time.time()
    with TestClient(app) as client:
        print("\n\n" + "-" * 50 + "\n")

        # User tests
        # Make a print of the test name, around a line of dashes
        print("\n" + "=" * 40)
        print(" " * 8 + "USER INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in user_test_functions]

    with TestClient(app) as client:
        # Recipe tests
        print("\n" + "=" * 40)
        print(" " * 8 + "RECIPE INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")
        
        [run_single_test(test_func, client) for test_func in recipe_test_functions]

    with TestClient(app) as client:
        # Review tests
        print("\n" + "=" * 40)
        print(" " * 8 + "REVIEW INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in review_test_functions]

    with TestClient(app) as client:
        # Collection tests
        print("\n" + "=" * 40)
        print(" " * 8 + "COLLECTION INTEGRATION TESTS" + " " * 12)
        print("=" * 40 + "\n")

        [run_single_test(test_func, client) for test_func in collections_test_functions]

    settings.TEST_ENV = False
    end = time.time()
    print(f"\nTotal time taken (Integration Tests): {end - start} seconds")

    # Security tests
    print("\n\n" + "-" * 50 + "\n")

    print("\n" + "=" * 40)
    print(" " * 12 + "SECURITY TESTS" + " " * 12)
    print("=" * 40 + "\n")
    [run_single_test(test_func, client, True) for test_func in security_hashing_test_functions]

    # Token tests
    print("\n" + "=" * 40)
    print(" " * 12 + "TOKEN TESTS" + " " * 12)
    print("=" * 40 + "\n")
    [run_single_test(test_func, client, True) for test_func in token_test_functions]

    cov.stop()
    cov.save()

    print("\n\n" + "-" * 50 + "\n")
    print("Total coverage report:")

    cov.report()

if __name__ == "__main__":
    run_tests()
