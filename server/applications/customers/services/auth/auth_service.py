#File for the helper/dependency functions for auth and routes
import string 
import random
from pydantic_extra_types.phone_numbers import PhoneNumber

"""Helper functions for the auth routes"""
#function to generate user six digit code
def generate_code(limit:int=6):
    code = ''.join(random.choices(k=limit), string.digits)

    return code #returns random six digit num

#function to send sms with twilio api
def send_message(user_number:PhoneNumber, pine_number=_, body:str):
    pass
    