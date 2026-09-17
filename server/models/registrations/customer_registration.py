#File for the SQL model for the customers registration
from sqlalchemy import (
    String, 
    DateTime
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from datetime import datetime

"""SQL model maps to table -> Postgres"""
class CustomerRegisterModelS():
    pass