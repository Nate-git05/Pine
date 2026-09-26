#File for the route for the customer chatting with the agent
from fastapi.routing import APIRouter

customer_home_router = APIRouter(prefix='/customer/home', tags=['Routes for the app\'s home page'])