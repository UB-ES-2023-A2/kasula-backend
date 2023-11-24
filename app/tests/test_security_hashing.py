import bcrypt
from app.utils.security import hash_password, verify_password  # Replace with your actual import

def test_hash_password():
    password = "securepassword123"
    hashed = hash_password(password)

    assert isinstance(hashed, str), "Hashed password should be a string"
    assert hashed != password, "Hashed password should not be the same as the plain password"

def test_verify_password():
    password = "securepassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)

    assert verify_password(password, hashed), "Verification should succeed for the correct password"
    assert not verify_password(wrong_password, hashed), "Verification should fail for the wrong password"
    assert not verify_password("", hashed), "Verification should fail for an empty password"

