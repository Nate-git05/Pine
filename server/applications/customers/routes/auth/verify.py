#File for the verification route for the customer's sms code 
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.routes.auth.signup import customer_auth_router
from server.applications.customers.schemas.auth.signup import (
    
)