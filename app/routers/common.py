from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.utils.security import hash_password, verify_password
from app.utils.token import create_access_token, get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId