#File for the SQL model for the transaction made by the customer
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String,
    DateTime,
    Integer,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from uuid import UUID
from datetime import datetime

"""SQL model for the agent job payments -> maps to table Postgres"""
class JobPayments(Base):
    __tablename__ = 'job_payments' #name for table in Postgres

    #defining attributes of the table 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    job_name:Mapped[str] = mapped_column(String(length=20), nullable=False)
    job_description:Mapped[str] = mapped_column(String(length=100), nullable=False)
    job_price:Mapped[int] = mapped_column(Integer, nullable=False)

    #relationship attributes 
    agent_job_id:Mapped[UUID] = mapped_column(ForeignKey('agent_jobs.id'), nullable=False)
    hired_agent_id:Mapped[UUID] = mapped_column(ForeignKey('hired_agents.id'), nullable=False)
    customer_id:Mapped[UUID] = mapped_column(ForeignKey('customers.id'), nullable=False)
    hired_agent_name:Mapped[str] = mapped_column()

    #audit attributes 
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)