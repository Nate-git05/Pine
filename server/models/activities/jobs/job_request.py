#File for the SQL model for the agent request to the customer for a job
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
from uuid import UUID
from enum import StrEnum
from datetime import datetime

"""Enum for the state of the job request"""
class JobRequestState(StrEnum):
    HANDLED='handled'
    NOT_HANDLED='not_handled'

"""SQL model maps agents job request -> Postgres model"""
class AgentJobRequest(Base):
    __tablename__ = 'job_requests' #name of table in Postgres

    #defining attributes of the model 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True) #unique identifier
    job_summary:Mapped[str] = mapped_column(String(length=100), nullable=False)

    #request attributes 
    request_name:Mapped[str] = mapped_column(String(length=25), nullable=False)
    request_description:Mapped[str] = mapped_column(String(length=100), nullable=False)
    customer_request_response:Mapped[str] = mapped_column(String(length=150), nullable=True)

    #state of the job request
    job_request_state:JobRequestState = mapped_column(String(length=15), nullable=False)

    #relationship attributes
    hired_agent_id:Mapped[UUID] = mapped_column(ForeignKey('hired_agents.id'), nullable=False)
    agent_job_id:Mapped[UUID] = mapped_column(ForeignKey('agent_jobs.id'), nullable=False)
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)

    #audit attributes 
    request_made_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    handled_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)