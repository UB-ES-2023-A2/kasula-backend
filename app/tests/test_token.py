import unittest
from unittest.mock import patch
from datetime import timedelta
import os

from app.utils.token import create_access_token, get_current_user
from fastapi.exceptions import HTTPException
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

@patch.dict(os.environ, {"SECRET_KEY": "your-secret-key"})
def test_create_access_token_default_expires():
    token = create_access_token(data={}, user_id="123", username="testuser")
    assert token is not None

@patch.dict(os.environ, {"SECRET_KEY": "your-secret-key"})
def test_create_access_token_custom_expires():
    custom_time = timedelta(minutes=30)
    token = create_access_token(data={}, user_id="123", username="testuser", expires_delta=custom_time)
    assert token is not None

@patch.dict(os.environ, {"SECRET_KEY": "your-secret-key"})
def test_create_access_token_with_additional_data():
    token = create_access_token(data={"extra": "data"}, user_id="123", username="testuser")
    assert token is not None