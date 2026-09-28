#File for the service helpers in the search route 
from server.applications.customers.schemas.pages.search_schema import AgentReturned
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from server.models.agents.hired_agent import HiredAgent
from server.models.activities.jobs.agent_job import (
    AgentJob,
    AgentJobState
)
from server.models.agents.agent import Agent

"""Helper function -> help with large/repeated blocks of code in route"""
#retrieves agent data -> pydantic model from payload from vector search 
async def retrieve_queryied_agents(payload_lst:list[dict]):
    returned_agents_lst = [] #lst to store the returned agents

    #looping payloads from vector db -> storing in returned lst
    for payload in payload_lst:
        #casting the str ids -> UUID
        agent_returned = AgentReturned(
            agent_id=payload.get('agent_id'),
            agent_price=(payload.get('agent_price') / 100),
            agent_name=payload.get('agent_name'),
            agent_description=payload.get('agent_description')
        )

        returned_agents_lst.append(agent_returned) #appending the agent to lst

    return returned_agents_lst

#updates the list for the agent seen ids 
def update_agent_ids_lst(payload_lst:list[dict], ids_lst:list):
    for payload in payload_lst:
        agent_id = payload.get('agent_id') #retrieving agent id from payload

        ids_lst.append(agent_id) #appending id to the lst

    return ids_lst #retrning the updated lst

#helper function to retrieve the agent rating across its jobs 
async def get_agents_rating(agent:Agent, session_db:AsyncSession) -> float:
    #database query -> agents job ids 
    agent_rating = None #flag for the rating

    try:
        agent_hired_query = await session_db.execute(select(HiredAgent).where(
            HiredAgent.agent_id == agent.id
        ))
        hired_agents_from_id = agent_hired_query.scalars().all() #getting all the hired agents from its id
    except Exception as error:
        raise error 

    #check if agent was hired before 
    if not hired_agents_from_id:
        agent_rating = 0.0 #no rating for the agent 
        return agent_rating

    #variables for the entire job and rating history
    agent_total_jobs = 0
    agent_total_rating = 0
    for hired_agent in hired_agents_from_id:
        try:
            agent_jobs_query = await session_db.execute(select(AgentJob).where(and_(
                AgentJob.hired_agent_id == hired_agent.id,
                AgentJob.job_state == AgentJobState.DONE
            )))
            agent_jobs = agent_jobs_query.scalars().all() #getting all the jobs from agent by id 
        except Exception as error:
            raise error 

        #check if the agent has completed a job 
        if not agent_jobs:
            continue #onto next agent hired 

        #getting the total rating throughout the job
        for job in agent_jobs:
            #checking if the job has a rating 
            if job.job_rating:
                agent_total_jobs += 1 #incrementing the jobs by one 
                agent_total_rating += job.job_rating 

    agent_rating = (agent_total_rating / agent_total_jobs) if agent_total_jobs else 0.0
    return agent_rating
