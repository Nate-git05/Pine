#File for the SQL model for the gmail integration
from server.config.configuration import Base
from server.applications.customers.schemas.pages.profile_schemas import EmailIntegrationType
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
from uuid import UUID, uuid4
from pydantic import EmailStr
from datetime import datetime

"""SQL model maps the gmail integration -> Postgres"""
class GmailIntegration(Base):
    __tablename__ = 'gmail_integration' #name of the table

    #defining attributes
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4) #unique identifier
    name:Mapped[str] = mapped_column(String, nullable=False)
    integrated_email:EmailStr = mapped_column(String, nullable=False, index=True, unique=True)
    integration_type:EmailIntegrationType = mapped_column(String, nullable=False)

    #oauth2 attributes
    oauth2_token:Mapped[str] = mapped_column(String, nullable=False)
    refresh_token:Mapped[str] = mapped_column(String, nullable=False)
    token_exp_time:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    #relationship attributes
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)

    #audit attributes
    integrated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used:Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_expired_at:Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_refreshed_at:Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
