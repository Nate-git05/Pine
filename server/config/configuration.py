#Configuration file for the server -> APIs, Database URIS, ...
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv() #loading the .env variables -> to memory

"""Configuring the database's server info"""
#Relational -> Postgres
class Base(DeclarativeBase):
    pass

POSTGRES_URI = os.getenv('POSTGRES_URI')
if not POSTGRES_URI:
    raise ValueError('Unable to retrieve the Postgres URI from .env file.')

#Cache -> Redis 
CACHE_URL = os.getenv('CACHE_URL')
CACHE_PORT = os.getenv('CACHE_PORT')
if (not CACHE_URL) or (not CACHE_PORT):
    raise ValueError('Unable to retrieve neither the url nor the port for the cache database from .env file.')

"""Configuring the API's for the server"""
#Twilio API
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_API_KEY = os.getenv('TWILIO_API_KEY')
TWILIO_SECRET = os.getenv('TWILIO_SECRET')
if (not TWILIO_ACCOUNT_SID) or (not TWILIO_API_KEY) or (not TWILIO_SECRET):
    raise ValueError('Unable to retrieve Twilio api information from .env file.')