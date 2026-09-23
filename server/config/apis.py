#File for wrapper for the servers apis's
from twilio.rest import Client
from server.config.configuration import (
    TWILIO_SECRET,
    TWILIO_API_KEY,
    TWILIO_ACCOUNT_SID
)
from openai import AsyncClient
from server.config.configuration import OPENAI_API_KEY

"""Configuring the API wrapper for apis used in the server"""
class APIWrapper:
    def __init__(self):
        self.twilio_client = None #flag for twilio client api

    #configuring twilio api client
    def configure_twilio_api(self,account_sid=TWILIO_ACCOUNT_SID,
                             api_key=TWILIO_API_KEY,
                             secret=TWILIO_SECRET) -> Client:
        self.twilio_client = Client(
                username=api_key,
                password=secret,
                account_sid=account_sid
            )
        
        return self.twilio_client #returns the api client for twilio

    #configuring the openai API
    def configure_openai_api(self, api_key:str=OPENAI_API_KEY):
        try:
            openai_client = AsyncClient(
                api_key=OPENAI_API_KEY
            )
        except Exception as error:
            raise error

        return openai_client #returning the openai client