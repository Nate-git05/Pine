#Configuration file for the server -> APIs, Database URIS, ...
from dotenv import load_dotenv
import os


"""Configuring the database's server info"""
#Relational -> Postgres
POSTGRES_URI = os.getenv('POSTGRES_URI')
if not POSTGRES_URI:
    raise ValueError('Unable to retrieve the Postgres URI from .env file.')