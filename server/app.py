#File for starting up the application for the server
from fastapi import FastAPI
from fastapi.requests import Request
from server.config.configuration import POSTGRES_URI
from server.config.database import (
    RelationalDatabase
)
from contextlib import asynccontextmanager

#getter functions for retrieving app states
async def get_relational_db_session(request:Request):
    relational_database:RelationalDatabase = request.app.state.relational_database

    #looping through database to retriev session
    async for session in relational_database.get_db():
        yield session
        break #yields only one session


#app's lifespan function -> configures the servers attributes at startup time
@asynccontextmanager
async def lifespan(app:FastAPI):
    #configuring the servers relational database
    relational_database = RelationalDatabase(
        postgres_uri=POSTGRES_URI
    )
    app.state.relational_datbase = relational_database #setting the POstgres wrapper as state 

    yield #yields the application running 


#Initialzing the app 
app = FastAPI(lifespan=lifespan)