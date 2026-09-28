#File for the SQL model for the customer/merchant session auth 
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String,
    DateTime,
    ForeignKey,
    LargeBinary
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime
import uuid

"""SQL model to map session auth -> Postgres"""
class SessionAuthentication(Base):
    #defining the attributes of the model 
    __tablename__ = 'session_authentication'

    #personal attributes 
    id:Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)

    #relationship attributes 
    customer_id:Mapped[uuid.UUID] = mapped_column(ForeignKey('customers.id'), nullable=True)
    merchant_id:Mapped[uuid.UUID] = mapped_column(ForeignKey('merchants.id'), nullable=True)

    #token attributes
    session_token:Mapped[bytes] = mapped_column(LargeBinary, nullable=False, unique=True, index=True)
    token_exp_time:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    #audit attributes
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
