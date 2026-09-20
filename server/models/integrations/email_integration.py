#SQL model for the email integration for Pine 
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column
)
from pydantic import EmailStr
from datetime import datetime
from uuid import UUID
from enum import StrEnum

#Enum for assigning the state of integrated email
class EmailIntegrationState(StrEnum):
    CONNECTED='connected'
    DISCONNECTED='disconnected'

#Python class for the email integration mapped -> Postgres
class EmailIntegration(Base):
    __tablename__ = 'email_integration'

    #defining personal attributes 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)
    email:EmailStr = mapped_column(String(length=100), nullable=False, index=True)

    #defining the relationaship params 
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)

    #defining the state of the integration
    integration_state:EmailIntegrationState = mapped_column(String(length=20), nullable=False)

    #audit attributes for the model
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    connected_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at:Mapped[datetime] = mapped_column(DateTime(timezone=True)nullable=True)

