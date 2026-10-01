"""Request and response schemas for merchant landing-page registration."""
import re

from pydantic import BaseModel, EmailStr, field_validator, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumber


class MerchantRegistration(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phonenumber: PhoneNumber

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError('Please enter a valid name.')
        if len(name) > 50:
            raise ValueError('Names cannot exceed 50 characters.')
        if not re.fullmatch(r'^[A-Za-z\s\-]+$', name):
            raise ValueError('Names may contain only letters, spaces, and hyphens.')
        return name.title()

    @model_validator(mode='after')
    def registration_fields_check(self):
        if not all([self.first_name, self.last_name, self.email, self.phonenumber]):
            raise ValueError('All fields must be entered to register.')
        return self


class MerchantRegistrationResponse(BaseModel):
    response: str
