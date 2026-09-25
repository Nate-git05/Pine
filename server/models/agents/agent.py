#SQL file for the agent table in Postgres
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String,
    ARRAY,
    DateTime,
    ForeignKey,
    Integer,
    Double
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
from enum import StrEnum
from uuid import UUID

"""Enum to define the state of the agent"""
class AgentState(StrEnum):
    ACTIVE='active'
    IDLE='idle'
    FIRED='fired'

"""SQL model for the agent maps python obj -> Postgres"""
class Agent(Base):
    __tablename__ = 'agents' #name for the agent's table

    #defining attributes of the agent 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)

    #personal attributes 
    name:Mapped[str] = mapped_column(String(length=50), nullable=True)
    description:Mapped[str] = mapped_column(String(length=100), nullable=False)
    agent_skills:Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), nullable=False)

    #agent tied info 
    agent_state:AgentState = mapped_column(String(length=20), nullable=False, index=True) 
    agent_rating:float = mapped_column(Double, nullable=False)
    agent_price_per_job:Mapped[int] = mapped_column(Integer, nullable=False)

    #relationaship attributes 
    merchant_id:Mapped[Uuid] = mapped_column(ForeignKey('merchants.id'), nullable=False, index=True)

    #storage database attributes 
    imgicon_storage_key:Mapped[str] = mapped_column(String(length=150), nullable=True)
    skill_file_storage_key:Mapped[str] = mapped_column(String(length=150), nullable=True)

    #url where to send the webhooks
    agents_webhook_url:Mapped[str] = mapped_column(String, nullable=False)

    #audit attributes 
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)