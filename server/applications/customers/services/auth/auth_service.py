#File for the helper/dependency functions for auth and routes
import string 
import random
from pydantic_extra_types.phone_numbers import PhoneNumber
from twilio.rest import Client
from enum import StrEnum

"""Helper functions for the auth routes"""
#function to generate user six digit code
def generate_code(limit:int=6):
    code = ''.join(random.choices(string.digits, k=limit))

    return code #returns random six digit num

#function to send sms with twilio api
def send_message(twilio_client:Client, user_number:PhoneNumber, 
                 pine_number:PhoneNumber, body:str):
    try:
        _ = twilio_client.messages.create(
            to=pine_number,
            from_=pine_number,
            body=body
        )
    except RuntimeError as error:
        raise error

"""Enum to define the state of the auth"""
class AuthState(StrEnum):
    SIGNUP='signup'
    LOGIN='login'