from fastapi import APIRouter, Body, Request, HTTPException, status, Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder