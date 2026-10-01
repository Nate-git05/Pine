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
    @staticmethod
    def configure_stripe_client(
            api_key:str=STRIPE_API_KEY
        ) -> StripeClient:
        stripe_client = StripeClient(
            api_key=api_key
        )

        return stripe_client

#Wrappper for the server notification events 
class NotificationEvents:
    def __init__(self):
        self.events:dict[str, Event] = {}
        self.queues:dict[str, Queue] = {}

    def _get_channel(self, customer_id:str) -> tuple[Event, Queue]:
        if customer_id not in self.events:
            self.events[customer_id] = Event()
            self.queues[customer_id] = Queue()
        return self.events[customer_id], self.queues[customer_id]

    #method flips event to wait 
    async def event_wait(self, customer_id:str):
        event, _ = self._get_channel(customer_id)
        await event.wait()

    #method to flip event to set 
    async def event_set(self, data:dict):
        customer_id = data.get('customer_id')
        if not customer_id:
            raise ValueError('Notification events require a customer_id.')
        event, queue = self._get_channel(str(customer_id))
        try:
            await queue.put(data)
            event.set()
        except Exception as error:
            raise error 

    #delete from queue 
    async def get_item(self, customer_id:str):
        event, queue = self._get_channel(customer_id)
        item = await queue.get()
        if queue.empty():
            event.clear()
        return item

#Wrapper for the Incoming job events
class IncomingJobsEvents:
    def __init__(self):
        self.events:dict[str, Event] = {}
        self.queues:dict[str, Queue] = {}

    def _get_channel(self, customer_id:str) -> tuple[Event, Queue]:
        if customer_id not in self.events:
            self.events[customer_id] = Event()
            self.queues[customer_id] = Queue()
        return self.events[customer_id], self.queues[customer_id]

    #method flips event to wait 
    async def event_wait(self, customer_id:str):
        event, _ = self._get_channel(customer_id)
        await event.wait()

    #method to flip event to set 
    async def event_set(self, data:dict):
        customer_id = data.get('customer_id')
        if not customer_id:
            raise ValueError('Incoming job events require a customer_id.')
        event, queue = self._get_channel(str(customer_id))
        try:
            await queue.put(data)
            event.set()
        except Exception as error:
            raise error 

    #delete from queue 
    async def get_item(self, customer_id:str):
        event, queue = self._get_channel(customer_id)
        item = await queue.get()
        if queue.empty():
            event.clear()
        return item
