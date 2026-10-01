"""SQL model for merchant interest registrations from the landing page."""
from datetime import datetime

from server.config.configuration import Base
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


class MerchantRegistrationModel(Base):
    __tablename__ = 'merchant_registration'

    first_name: Mapped[str] = mapped_column(String(length=50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=50), nullable=False)
    email: Mapped[str] = mapped_column(String(length=254), primary_key=True, index=True)
    phonenumber: Mapped[str] = mapped_column(String(length=15), primary_key=True, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
