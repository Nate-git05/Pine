#File for the service helpers in the search route 
from server.applications.customers.schemas.pages.search_schema import AgentReturned

"""Helper function -> help with large/repeated blocks of code in route"""
#retrieves agent data -> pydantic model from payload from vector search 
async def retrieve_queryied_agents(payload_lst:list[dict]):
    returned_agents_lst = [] #lst to store the returned agents

    #looping payloads from vector db -> storing in returned lst
    for payload in payload_lst:
        #casting the str ids -> UUID
        agent_returned = AgentReturned(
            agent_id=payload.get('agent_id'),
            agent_name=payload.get('agent_name'),
            agent_description=payload.get('agent_desciption')
        )

        returned_agents_lst.append(agent_returned) #appending the agent to lst

    return returned_agents_lst

#updates the list for the agent seen ids 
def update_agent_ids_lst(payload_lst:list[dict], ids_lst:list):
    for payload in payload_lst:
        agent_id = payload.get('agent_id') #retrieving agent id from payload

        ids_lst.append(agent_id) #appending id to the lst

    return ids_lst #retrning the updated lst