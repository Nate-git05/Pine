#File for the SQL model for the agents job
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String,
    DateTime,
    ForeignKey,
    Integer
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime
from enum import StrEnum
from uuid import UUID

"""Enum for the state of the job"""
class AgentJobState(StrEnum):
    ACTIVE='active'
    DONE='done'

"""SQL model for the agent job maps -> Postgres table"""
class AgentJob(Base):
    __tablename__ = 'agent_jobs' #name of the table 

    #defining attributes of the model
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True) #unique identifier for the job 
    job_name:Mapped[str] = mapped_column(String(length=20), nullable=False)
    job_description:Mapped[str] = mapped_column(String(length=100), nullable=True)

    #state and price attributes for the job
    job_state:AgentJobState = mapped_column(String(length=10), nullable=False)
    job_price:Mapped[int] = mapped_column(Integer, nullable=False)
    job_rating:Mapped[int] = mapped_column(Integer, nullable=False) 

    #relationship params for the job
    hired_agent_id:Mapped[UUID] = mapped_column(ForeignKey('hired_agents.id'), nullable=False)
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('hired_agents.id'), nullable=False)

    #audit attributes 
    assigned_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_help:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)