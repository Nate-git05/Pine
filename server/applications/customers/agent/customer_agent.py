#File for the customer Pine agent 
from agents import (
    Agent,
    Runner
)
from dataclasses import dataclass 
from enum import StrEnum
from pydantic import BaseModel
from pathlib import Path
from server.config.database import (
    CacheDatabase,
    RelationalDatabase
)
from typing import Any
import json

"""Enum to classify the type of message from customer"""
class MessageType(StrEnum):
    JOBCREATION='job_creation'
    CONVERSATION='conversation'
    INFORMATIVE='informative'
    HARMFUL='harmful'
    SUPPORT='support'

#Formated output for routing agent
class AgentOutput(BaseModel):
    message_type:MessageType | None = None 
    response:str | None = None 

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

"""Enum for the type of agent"""
class AgentType(StrEnum):
    ROUTER='router'
    TOOLING='tooling'

"""Defining the Pine Agent model"""
class PineAgent:
    def __init__(self, 
                 routing_agent:str = None,
                 tooling_agent:str = None,
                 relational_db:RelationalDatabase = None,
                 cache_db:CacheDatabase = None):
        #defining the attributes 
        self.routing_agent = routing_agent
        self.tooling_agent = tooling_agent

        #data structures attributes  
        self.skill_file_map = {}
        self.agent_tool_lst = []

    #static method to retrieve context for the router/tooling agent
    @staticmethod
    async def get_context(self, cache_key:str, 
                             agent_type:AgentType,
                             cache_db:CacheDatabase):
        #matching the agent type with case 
        try:
            match agent_type:
                case AgentType.ROUTER:
                    router_context = await cache_db.retrieve_lst(
                        key=cache_key
                    )
                    if not router_context:
                        return ''

                    #context -> str for agent message 
                    return router_context

                #case for the tooling agent 
                case AgentType.TOOLING:
                    tooling_agent_context = await cache_db.retrieve_lst(
                        key=cache_key
                    )
                    if not tooling_agent_context:
                        return '' #empty string if no context

                    return tooling_agent_context
        except Exception as error:
            raise error

    #static method to store context 
    @staticmethod
    async def store_context(self, cache_key:str,
                            agent_type:AgentType,
                            cache_value:Any,
                            cache_db:CacheDatabase):
        try:
            match agent_type:
                case AgentType.ROUTER:
                    await cache_db.insert_list(
                        key=cache_key,
                        value=json.dumps(cache_value),
                        exp_time=1200
                    )
                    return

                #matching the tooling agent 
                case AgentType.TOOLING:
                    await cache_db.insert_list(
                        key=cache_key,
                        value=json.dumps(cache_value)
                    )
                    return
        except Exception as error:
            raise error
                
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
    async def run_router_agent(self, router_message:str, agent_name:str='router_agent'):
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
            name=agent_name,
            prompt=router_skill,
            model=self.routing_agent,
            output_type=AgentOutput
        )

        #running the agent on customer message 
        try:
            agent_result = await Runner.run(
                router_agent,
                router_message
            )
        except Exception as error:
            raise error 

        message_type:MessageType = agent_result.final_output #getting format output from agent run
        return message_type

    #creating the tooling agent 
    async def run_tooling_agent(self, 
                                agent_message:AgentMessage,
                                agent_name:str='tooling_agent'):
        try:
            agent_skill = self.get_agent_skill(
                message_type=agent_message.message_type,
                router=None
            )
        except Exception as error:
            raise error 

        #creating the tooling agent 
        tooling_agent = Agent(
            name=agent_name,
            model=self.tooling_agent,
            instructions=agent_skill,
            tools=self.agent_tool_lst,
            output_type=AgentOutput
        )

        #running the tool agent 
        try:
            result = await Runner.run(
                tooling_agent,
                agent_message.message
            )
        except Exception as error:
            raise error 

        #getting agent response 
        agent_response:AgentOutput = result.final_output
        return agent_response