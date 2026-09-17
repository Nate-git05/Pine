#File for the SQL model for the sms verification
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String, 
    DateTime,
    Integer,
    LargeBinary
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from pydantic_extra_types.phone_numbers import PhoneNumber
import uuid
from datetime import datetime
from enum import StrEnum
import bcrypt

"""Enum for the state of the verification"""
class VerificationState(StrEnum):
    PENDING='pending'
    ACCEPTED='accepted'

"""Python model maps to table in Posgres"""
class SMSVerification(Base):
    #defining attributes of the model
    __tablename__ = 'sms_verification' #name for table 

    #defining personal attributes of table 
    id:Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)
    phonenumber:PhoneNumber = mapped_column(String(length=15), nullable=False)

    #configuring attributes for the sms verfication
    verification_code:Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    verification_attempts:Mapped[int] = mapped_column(Integer, nullable=False)
    verification_state:VerificationState = mapped_column(String(length=10), nullable=False)

    #audit attributes of the verification
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)