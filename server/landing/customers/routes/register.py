#File for the customer registration route 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.app import get_relational_db_session
