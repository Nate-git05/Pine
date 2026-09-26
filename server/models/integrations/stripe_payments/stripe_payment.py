#SQl model for the stripe payment 
from server.config.configuration import Base
from sqlalchemy import (
    Uuid, 
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from enum import StrEnum
from uuid import UUID
from datetime import datetime

"""Enum for the state of the payment"""
class PaymentState(StrEnum):
    ACTIVE='active'
    INACTIVE='inactive'

"""SQL model maps stipe payment -> Postgres"""
class StripePayment(Base):
    __tablename__ = 'stripe_payments' #name of table in Postgres

    #defining attributes of the model
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)
    stripe_customer_id:Mapped[str] = mapped_column(String(length=100), nullable=False)

    #state of the payment -> active/inactive
    payment_state:PaymentState = mapped_column(String(length=20), nullable=False, index=True)

    #relationship attributes 
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)
    merchant_id:Mapped[UUID] = mapped_column(ForeignKey('merchants.id'), nullable=False)

    #audit attributes
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
