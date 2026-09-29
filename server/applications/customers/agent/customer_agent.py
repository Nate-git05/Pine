#File for the customer Pine agent 
from agents import (
    Agent,
    Runner,
    function_tool
)
from dataclasses import dataclass 
from enum import StrEnum
from pydantic import BaseModel
from pathlib import Path

"""Enum to classify the type of message from customer"""
class MessageType(StrEnum):
    JOBCREATION='job_creation'
    CONVERSATION='conversation'
    INFORMATIVE='informative'
    HARMFUL='harmful'
    SUPPORT='support'

#Formated output for routing agent
class RoutingAgentOutput(BaseModel):
    message_type:MessageType = None 

#Defining the message for the agent 
@dataclass
class AgentMessage:
    message_type:MessageType = None 
    message:str = None

#helper functions for the static methods 
def get_skill_content(skill_path:Path):
    #checking if path is a found file 
    if not skill_path.is_file():
        raise ValueError('')

    #retrieve the content from the path 
    with open(skill_path, mode='r') as file:
        skill_content = file.read()

    #check if content was returned 
    if not skill_content:
        raise ValueError('')

    return skill_content #returning content of the file

"""Defining the Pine Agent model"""
class PineAgent:
    def __init__(self, routing_agent:str = None,
                 tooling_agent:str = None, 
                 tooling_lst:list = None):
        #defining the attributes 
        self.routing_agent = routing_agent
        self.tooling_agent = tooling_agent

        #map attributes 
        self.skill_file_map = {}
        self.agent_tool_map = {}

    #Method to retrieve the skill for the agent 
    def get_agent_skill(self, message_type:MessageType | None = None, router:bool | None =None):
        #getting agent's skill
        if router:
            skill_path = self.skill_file_map.get('router') #file path for skill
            if not skill_path:
                raise ValueError('')

            router_skill = get_skill_content(skill_path)
            return router_skill #

        #getting the agent skill path from message type 
        skill_path = self.skill_file_map.get(message_type)
        if not skill_path:
            raise ValueError('')

        agent_skill = get_skill_content(skill_path) #skill content
        return agent_skill

    #method to create and run -> routing agent
    async def run_router_agent(self, customer_message:str, agent_name:str='router_agent'):
        #getting the router skill
        try:
            router_skill = self.get_agent_skill(
                message_type=None,
                router=True
            )
        except Exception as error:
            raise error

        #creating the router agent
        router_agent = Agent(
            name=router_agent,
            prompt=router_skill,
            model=self.routing_agent,
            output_type=RoutingAgentOutput
        )

        #running the agent on customer message 
        try:
            agent_result = await Runner.run(
                router_agent,
                customer_message
            )
        except Exception as error:
            raise error 

        message_type:MessageType = agent_result.final_output #getting format output from agent run

        #creating the tooling agent message 
        tooling_agent_message = AgentMessage(
            message_type=message_type,
            message=customer_message
        )
        return tooling_agent_message #returning the agent's message 