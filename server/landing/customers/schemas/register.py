#Schema file for the customer's landing page 
from pydantic import (
    BaseModel,
    EmailStr,
    model_validator,
    field_validator
)
from pydantic_extra_types.phone_numbers import PhoneNumber
import re

#defining the schema for the customer's registration
class CustomerRegistration(BaseModel):
    #registration attributes 
    first_name:str = None 
    last_name:str = None 
    username:str = None 
    email:EmailStr = None 
    phonenumber:PhoneNumber = None 

    #validating the registration fields 
    @field_validator('first_name')
    @classmethod
    def firstname_check(cls, name:str) -> str:
        name = name.strip() #stripping leading/ending whitespace 
        if not name:
            raise ValueError('Please enter a valid first name.')

        #checking length of the name 
        if len(name) > 50:
            raise ValueError('The first name exceeds the max amount of 50 characters.')

        #checking the contents of the name
        pattern = r'^[A-Za-z\s\-]+$'
        if re.match(pattern, name):
            raise ValueError('The first name may not contain either a space, number, symbol.')

        return name.title #returns the name capitalized

    @field_validator('last_name')
    @classmethod
    def lastname_check(cls, name:str) -> str:
        name = name.strip() #stripping leading/ending whitespace 
        if not name:
            raise ValueError('Please enter a valid last name.')

        #checking length of the name 
        if len(name) > 50:
            raise ValueError('The last name exceeds max amount of 50 characters.')

        #checking the contents of the name
        pattern = r'^[A-Za-z\s\-]+$'
        if re.match(pattern, name):
            raise ValueError('The first name may not contain either a space, number, symbol.')

        return name.title #returns the name capitalized 

    @field_validator('username')
    @classmethod
    def username_check(cls, name:str) -> str:
        name = name.strip() #stripping any leading/ending whitespace 
        if not name:
            raise ValueError('Please enter valid username.')

        #checking the length of the name
        if len(name) > 50:
            raise ValueError('The username exceeds max amount of 50 characters.')

        return name #returning the username 

    #validating the schema model 
    @model_validator(mode='after')
    def customer_registration_check(self):
        #checking if all fields entered 
        if not all([
            self.first_name, self.last_name, self.username,
            self.email, self.phonenumber
        ]):
            raise ValueError('All fields must be entered to continue.')

        return self #returns the instance of the schema 