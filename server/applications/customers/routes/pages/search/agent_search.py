#File for the customer to search for the agent 
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from fastapi import Depends
from server.applications.customers.services.auth.auth_service import get_current_customer
from server.models.users.customers import Customer
from server.models.agents.agent import (
    Agent,
    AgentState
)
from server.models.agents.hired_agent import HiredAgent