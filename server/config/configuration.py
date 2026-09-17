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