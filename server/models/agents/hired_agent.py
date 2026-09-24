#SQL model for the customer's hired agent
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    ARRAY,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Double
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from server.models.agents.agent import AgentState
from sqlalchemy.ext.mutable import MutableList
from uuid import UUID
from datetime import datetime

"""Hired agent table -> maps to Postgres"""
class HiredAgent(Base):
    __tablename__ = 'hired_agents'

    #defining attributes in the table 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name:Mapped[str] = mapped_column(String(length=50), nullable=False)
    description:Mapped[str] = mapped_column(String(length=100), nullable=False)
    price_per_job:Mapped[str] = mapped_column(Integer, nullable=False)
    agent_rating:Mapped[float] = mapped_column(Double, nullable=False)

    #relationship attributes
    agent_id:Mapped[UUID] = mapped_column(ForeignKey('agents.id'), nullable=False)
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)

    #agent attributes for state and permissions
    agent_restrictions:Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), nullable=True)
    agent_state:AgentState = mapped_column(String(length=20), nullable=True)
    agent_imgicon_key:Mapped[str] = mapped_column(String(length=150), nullable=False)

    #audit attributes 
    hired_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fired_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)