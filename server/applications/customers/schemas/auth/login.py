#File for the schemas for the customer login
from pydantic import (
    BaseModel,
    EmailStr,
    model_validator
)
from pydantic_extra_types.phone_numbers import PhoneNumber

"""Schema for the login fields the customer enters"""
class CustomerLogin(BaseModel):
    #defining attributes of the model
    email:EmailStr = None 
    phonenumber:PhoneNumber = None

    #validating the model
    @model_validator(mode='after')
    def customer_login_check(self):
        #ensuring customer entered all fields 
        if not all([
            self.email, self.phonenumber
        ]):
            raise ValueError('Both email and phonenumber need to be entered to login.')
        return self
        
#Schema for the login response to the client
class CustomerLoginResponse(BaseModel):
    token:str = None 
    response:str = None


class CustomerLogoutResponse(BaseModel):
    response: str
