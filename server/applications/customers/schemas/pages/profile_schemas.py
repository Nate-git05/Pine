#File for the schemas for the customer profile page 
import strawberry

"""Strawberry schema for the graphql routes"""
@strawberry.type
class CustomerProfile:
    #customer attributes 
    customer_name:str = None 
    customer_email:str = None
    customer_number:str = None 

    #payment attribute 
    card_type:str = None
    active_card_last4:str = None 

    #agent/jobs attributes 
    number_of_agents:int = None 
    jobs_completed:int = None