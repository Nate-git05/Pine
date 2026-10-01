#File for the SQL model for the customer 
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
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
import uuid 

"""Python SQL model maps to table -> Postgres"""
class Customer(Base):
    #defining attributes of the table 
    __tablename__ = 'customers' #name for the table in postgres

    #personal attributes of the table 
    id:Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)

    #contact information 
    email:EmailStr = mapped_column(String(length=50), nullable=False, index=True, unique=True)
    phonenumber:PhoneNumber = mapped_column(String(length=15), nullable=False, index=False, unique=True)

    #Stripe customer identifier is stored independently of saved payment methods.
    stripe_customer_id:Mapped[str | None] = mapped_column(String(length=100), nullable=True, unique=True)

    #audit information
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
