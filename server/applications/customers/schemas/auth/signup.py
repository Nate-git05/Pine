#File for the signup auth schemas for the customer 
from pydantic import (
    BaseModel,
    EmailStr,
    model_validator,
    field_validator
)
from pydantic_extra_types.phone_numbers import PhoneNumber
import re

"""Schema defines the users signup page for auth"""
class CustomerSignup(BaseModel):
    #defining attributes of the model
    first_name:str = None 
    last_name:str = None
    email:EmailStr = None 
    phonenumber:PhoneNumber = None 

    #validating the entered fields 
    @field_validator('first_name')
    @classmethod
    def firstname_check(cls, name:str) -> str:
        name = name.strip() #stripping leading/ending whitespace 
        if not name:
            raise ValueError('Please enter a valid first name.')

        #checking the length of the name 
        if len(name) > 50:
            raise ValueError('The first name exceeds max amount of 50 characters')

        #checking contents of the name 
        pattern = r'^[A-Za-z\s\-]+$'
        if re.match(pattern, name):
            raise ValueError('The first name may not contain symbols, spaces, or numbers.')

        return name.title() #returns the name title cased 

    @field_validator('last_name')
    @classmethod
    def lastname_check(cls, name:str) -> str:
        name = name.strip()
        if not name:
            raise ValueError('Please enter a valid last name.')

        #checking length of the last name 
        if len(name) > 50:
            raise ValueError('The last name exceeds max amount of 50 characters.')

        #checking contents of last name 
        pattern = r'^[A-Za-z\s\-]+$'
        if re.match(pattern, name):
            raise ValueError('The last name may not contain symbols, spaces, or numbers.')

        return name.title() #returns the name title cased 

    #validating the schema model 
    @model_validator(mode='after')
    def customer_signup_check(self):
        #checking if all fields were entered 
        if not all([
            self.first_name, self.last_name,
            self.email, self.phonenumber
        ]):
            raise ValueError('All fields are required to complete signup.')

        return self #returning the signup schema

#Schema for the customer signup route
class CustomerSignupResponse(BaseModel):
    customer_token:str = None 
    response:str = None 

#Schema for the customer's verification code 
class CustomerSMSVerify(BaseModel):
    code:str = None 

    @field_validator('code')
    @classmethod
    def code_check(cls, user_code:str) -> str:
        user_code = user_code.strip() #stripping leadig/ending whitespace 
        if not user_code:
            raise ValueError('Please enter the verification code sent to you.')

        #checking length of code 
        if len(user_code) != 6:
            raise ValueError('Verification is incorrect. Please try again.')

        #ensuring code is only numbers 
        if not user_code.isdigit():
            raise ValueError('Verification is incorrect. Please try again.')

        return user_code #returning code entered by customer
