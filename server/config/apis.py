#File for wrapper for the servers apis's
from twilio.rest import Client
from server.config.configuration import (
    TWILIO_SECRET,
    TWILIO_API_KEY,
    TWILIO_ACCOUNT_SID
)
from openai import AsyncClient
from server.config.configuration import OPENAI_API_KEY
from asyncio import (
    Event, 
    Queue
)

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
                api_key=api_key
            )
        except Exception as error:
            raise error

        return openai_client #returning the openai client

#Wrappper for the server notification events 
class NotificationEvents:
    def __init__(self):
        self.notification_event = Event() #event obj for 
        self.async_queue = Queue()

    #method flips event to wait 
    async def event_wait(self):
        await self.notification_event.wait() #holds the event -> waits to be flipped 

    #method to flip event to set 
    async def event_set(self, data:dict):
        #appending data to the async queue
        try:
            await self.async_queue.put(data) #signifies to the event the data 
            await self.notification_event.set() #starts the event
        except Exception as error:
            raise error 

    #delete from queue 
    async def get_item(self):
        if not self.async_queue:
            return 

        #else
        try:
            item = await self.async_queue.get()
            return item #returning item in queue 
        except Exception as error:
            raise error