from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.utils.security import hash_password, verify_password
from app.utils.token import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
import warnings
import re
from pydantic import BaseModel