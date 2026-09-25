#File for the SQL model for the merchants API info 
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
from uuid import UUID
import hmac
import hashlib

"""SQL model for the merchants API auth"""
class MerchantAPI(Base):
    __tablename__ = 'merchant_api' #name of the tablename 

    #defining attributes -> of the SQL 
    id:Mapped[UUID] = mapped_column(Uuid, primary_key=True) #unique identifier 
    api_key:Mapped[UUID] = mapped_column(Uuid, unique=True, nullable=False, index=True)

    #relationship attributes 
    merchant_id:Mapped[UUID] = mapped_column(ForeignKey('merchants.id'))

    #audit attributes 
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validated_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    #method to get the signature of the hash 
    def get_merchant_signature(self, data:str) -> str:
        encoded_data = data.encode('utf-8') #getting the data as bytes 

        #getting the hmac signature 
        signature = hmac.new(
            key=self.api_key.bytes,
            msg=encoded_data,
            digestmod=hashlib.sha256
        )
        return signature #returning signature 

    #method to check the hash to confirm 
    def check_signature(self, data:str, api_signature:str) -> bool:
        encoded_data = data.encode('utf-8') #getting data as bytes 

        #getting the signature -> api key data 
        signature = hmac.new(
            self.api_key.bytes,
            encoded_data,
            hashlib.sha256
        )

        #returning the bool sig
        return hmac.compare_digest(
            api_signature,
            signature
        )       