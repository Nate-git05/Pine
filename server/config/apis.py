#File for wrapper for the servers apis's
from twilio.rest import Client
from server.config.configuration import (
    TWILIO_SECRET,
    TWILIO_API_KEY,
    TWILIO_ACCOUNT_SID,
    STRIPE_API_KEY
)
from openai import AsyncClient
from server.config.configuration import OPENAI_API_KEY
from asyncio import (
    Event, 
    Queue
)
from stripe import StripeClient

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

    #configuring the Stripe client
    def configure_stripe_client(
            api_key:str=STRIPE_API_KEY
        ):
        stripe_client = StripeClient(
            api_key=api_key
        )

        return stripe_client

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
        if self.async_queue.empty():
            return None 

        #else
        try:
            item = await self.async_queue.get()
            if self.async_queue.empty():
                self.notification_event.clear()
            return item #returning item in queue
        except Exception as error:
            raise error

#Wrapper for the Incoming job events
class IncomingJobsEvents:
    def __init__(self):
        self.jobs_event = Event()
        self.async_queue = Queue()

    #method flips event to wait 
    async def event_wait(self):
        await self.jobs_event.wait() #holds the event -> waits to be flipped 

    #method to flip event to set 
    async def event_set(self, data:dict):
        #appending data to the async queue
        try:
            await self.async_queue.put(data) #signifies to the event the data 
            await self.jobs_event.set() #starts the event
        except Exception as error:
            raise error 

    #delete from queue 
    async def get_item(self):
        if self.async_queue.empty():
            return None 

        #else
        try:
            item = await self.async_queue.get()
            if self.async_queue.empty():
                self.jobs_event.clear()
            return item #returning item in queue
        except Exception as error:
            raise error
