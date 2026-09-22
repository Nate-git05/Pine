#File for the service helpers in the search route 
from sqlalchemy.ext.asyncio import AsyncSession

"""Helper function -> help with large/repeated blocks of code in route"""
async def retrieve_queryied_agents(payload:list[dict], session_db:AsyncSession):
    returned_agents_lst = [] #lst to store the returned agents

    #looping payloads from vector db -> querying agent from relational db
    try:
        for agent in payload:
            pass 
    except RuntimeError as error:
        raise error
    pass