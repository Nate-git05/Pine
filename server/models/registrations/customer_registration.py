#File for the SQL model for the customers registration
from server.config.configuration import Base
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
class CustomerRegisterModel(Base): 
    #defining attrbutes of the model 
    __tablename__ = 'customer_registration' #name for table in Postgres

    #personal attributes of the model
    first_name:Mapped[str] = mapped_column(String(length=50), nullable=True)
    last_name:Mapped[str] = mapped_column(String(length=50), nullable=False)

    #contact info of the model 
    email:EmailStr = mapped_column(String(length=50), nullable=False, index=True, primary_key=True)
    phonenumber:PhoneNumber = mapped_column(String(length=15), nullable=False, index=True, primary_key=True)

    #audit info of the customer 
    registered_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)