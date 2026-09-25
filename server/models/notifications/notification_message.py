#File for the SQL model for the customer/merchants notifications
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
from datetime import datetime
from enum import StrEnum
from uuid import UUID

"""Enum for the type of the notification message"""
class NotificationType(StrEnum):
    AGENT_HIRED='agent_hired'
    JOB_COMPLETED='job_completed'
    JOB_ACTION='job_action'
    AGENT_UPDATE='agent_update'

"""Enum for the state of the notification"""
class NotificationState(StrEnum):
    READ='read'
    UNREAD='unread'

"""SQL model for notification maps to notification table -> Postgres"""
class Notification(Base):
    __tablename__ = 'notifications' #name of the table in Postgres

    #personal attributes of the notification model
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True) #unique identifier 
    notification_header:Mapped[str] = mapped_column(String(length=50), nullable=False)
    notification_message:Mapped[str] = mapped_column(String(length=150), nullable=False)

    #state and type attributes of the notification
    notification_type:NotificationState = mapped_column(String(length=15), nullable=False)
    notification_state:NotificationState = mapped_column(String(length=15), nullable=False)

    #relationship attributes 
    merchant_id:Mapped[UUID] = mapped_column(ForeignKey('merchants.id'), nullable=True)
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=True)
    job_id:Mapped[UUID] = mapped_column(ForeignKey('agent_jobs.id'), nullable=True)

    #audit attributes 
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    
    