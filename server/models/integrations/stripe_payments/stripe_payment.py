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
from uuid import UUID, uuid4
from datetime import datetime

"""SQL model maps stipe payment -> Postgres"""
class StripePayment(Base):
    __tablename__ = 'stripe_payments' #name of table in Postgres

    #defining attributes of the model
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)
    stripe_customer_id:Mapped[str] = mapped_column(String(length=100), nullable=False)
    stripe_payment_id:Mapped[str] = mapped_column(String(length=100), nullable=True)

    #relationship attributes 
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)

    #audit attributes
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used:Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
