#File for the SQL model for the merchants
from server.config.configuration import Base
from sqlalchemy import (
    Uuid,
    String
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from uuid import UUID

"""SQL model maps merchant -> Postgres"""
class Merchant(Base):
    __tablename__ = 'merchants' #name for the merchants table

    #defining personal attributes 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name:Mapped[str] = mapped_column(String(length=100), nullable=False)
    username:Mapped[str] = mapped_column(String(length=50), nullable=False)