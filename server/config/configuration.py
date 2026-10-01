#Configuration file for the server -> APIs, Database URIS, ...
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv() #loading the .env variables -> to memory

"""Configuring the database's server info"""
#Server's phonenumber
PINENUMBER = os.getenv('PINENUMBER')
if not PINENUMBER:
    raise ValueError('Unable to retrieve the server\'s phonenumber from .env file.')

#Server's secret key
SERVER_SECRET_KEY = os.getenv('SERVER_SECRET_KEY')
if not SERVER_SECRET_KEY:
    raise ValueError('Unable to retrieve the server\'s secret key.')

#Pine's client webhook URL -> creates the customer's job offer
CLIENT_WEBHOOK_URL = os.getenv('CLIENT_WEBHOOK_URL')
if not CLIENT_WEBHOOK_URL:
    raise ValueError('Unable to retrieve the URL for the client webhook.')

#Server's Stripe success/failed routes 
STRIPE_SUCCESS_ROUTE = os.getenv('STRIPE_SUCCESS_ROUTE')
STRIPE_CANCEL_ROUTE = os.getenv('sTRIPE_CANCEL_ROUTE')
if (not STRIPE_SUCCESS_ROUTE) or (not STRIPE_CANCEL_ROUTE):
    raise ValueError('Unable to retrieve the success nor cancel url for Stripe api from the .env file.')

#Getting the server's agents info 
ROUTER_AGENT = os.getenv('ROUTER_AGENT')
TOOLING_AGENT = os.getenv('TOOLING_AGENT')
if (not ROUTER_AGENT) or (not TOOLING_AGENT):
    raise ValueError('Unable to get either the router agent or tooling agent name from .env file.')

"""Configuring the server\'s databases"""
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

#Vector -> Qdrant 
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
if (not QDRANT_URL) or (not QDRANT_API_KEY):
    raise ValueError('Unable to retrieve the url and the api key for the Qdrant from .env file.')

"""Configuring the API's for the server"""
#Twilio API
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_API_KEY = os.getenv('TWILIO_API_KEY')
TWILIO_SECRET = os.getenv('TWILIO_SECRET')
if (not TWILIO_ACCOUNT_SID) or (not TWILIO_API_KEY) or (not TWILIO_SECRET):
    raise ValueError('Unable to retrieve Twilio api information from .env file.')

#OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
if (not EMBEDDING_MODEL) or (not OPENAI_API_KEY):
    raise ValueError('Unable to retrieve the OpenAI key nor the embedding model from the .env file.')

#Stripe API
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
if not STRIPE_API_KEY:
    raise ValueError('Unable to retrieve the Stripe api key from .env file.')

#Stripe webhook signing secret is configured when the Stripe endpoint is created.
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

#Google client API
GOOGLE_SCOPES_URL = os.getenv('GOOGLE_SCOPES_URL')
if not GOOGLE_SCOPES_URL:
    raise ValueError('Unable to retrieve scopes for google api from .env file.')
SCOPES = [GOOGLE_SCOPES_URL]

#Google redirect URL
GOOGLE_REDIRECT_URL = os.getenv('GOOGLE_REDIRECT_URL')
if not GOOGLE_REDIRECT_URL:
    raise ValueError('Unable to retrieve google redirect url from .env file.')

#The local file path can be replaced with a mounted Secret Manager file in Cloud Run.
GOOGLE_CLIENT_SECRET_FILE = os.getenv(
    'GOOGLE_CLIENT_SECRET_FILE',
    'client_secret.json'
)
