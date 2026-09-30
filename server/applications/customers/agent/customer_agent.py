#File for the customer Pine agent 
from agents import Agent, Runner
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from server.config.database import (
    CacheDatabase,
    RelationalDatabase
)
import json

"""Enum to classify the type of message from customer"""
class MessageType(StrEnum):
    JOBCREATION='job_creation'
    CONVERSATION='conversation'
    INFORMATIVE='informative'
    HARMFUL='harmful'
    UNKNOWN='unknown'
    SUPPORT='support'

# Structured output returned by the tooling agent.
class AgentOutput(BaseModel):
    response: str


# Structured output returned by the routing agent.
class RouterOutput(BaseModel):
    message_type: MessageType

#Defining the message for the agent 
@dataclass
class AgentMessage:
    message_type: MessageType
    message: str


class AgentConfigurationError(RuntimeError):
    """Raised when the agent is missing a required skill or model setting."""

#helper functions for the static methods 
def get_skill_content(skill_path: Path) -> str:
    # Check that the configured skill exists and contains instructions.
    if not skill_path.is_file():
        raise AgentConfigurationError(f'The configured skill file was not found: {skill_path.name}')

    with open(skill_path, mode='r', encoding='utf-8') as file:
        skill_content = file.read()

    if not skill_content:
        raise AgentConfigurationError(f'The configured skill file is empty: {skill_path.name}')

    return skill_content

"""Enum for the type of agent"""
class AgentType(StrEnum):
    ROUTER='router'
    TOOLING='tooling'


#Keep the router instructions separate from the tooling skill instructions.
SKILL_DIRECTORY = Path(__file__).parent / 'skills'
ROUTER_SKILL_DIRECTORY = SKILL_DIRECTORY / 'router'
TOOLING_SKILL_DIRECTORY = SKILL_DIRECTORY / 'tooling'
DEFAULT_SKILL_FILE_MAP: dict[MessageType | str, Path] = {
    'router': ROUTER_SKILL_DIRECTORY / 'router.md',
    MessageType.JOBCREATION: TOOLING_SKILL_DIRECTORY / 'job_creation.md',
    MessageType.CONVERSATION: TOOLING_SKILL_DIRECTORY / 'conversation.md',
    MessageType.INFORMATIVE: TOOLING_SKILL_DIRECTORY / 'informative.md',
    MessageType.HARMFUL: TOOLING_SKILL_DIRECTORY / 'harmful.md',
    MessageType.SUPPORT: TOOLING_SKILL_DIRECTORY / 'support.md',
    MessageType.UNKNOWN: TOOLING_SKILL_DIRECTORY / 'unknown.md',
}

"""Defining the Pine Agent model"""
class PineAgent:
    def __init__(self, 
                 routing_agent: str | None = None,
                 tooling_agent: str | None = None,
                 relational_db: RelationalDatabase | None = None,
                 cache_db: CacheDatabase | None = None,
                 skill_file_map: dict[MessageType | str, Path] = DEFAULT_SKILL_FILE_MAP,
                 agent_tool_lst: list[Any] | None = None):
        # Shared model and adapter settings are configured once at app startup.
        self.routing_agent = routing_agent
        self.tooling_agent = tooling_agent
        self.relational_db = relational_db
        self.cache_db = cache_db

        # Keep tool implementations optional while their files are being built.
        self.skill_file_map skill_file_map
        self.agent_tool_lst = agent_tool_lst or []

    # Read the agent's full conversation context without consuming the Redis list.
    @staticmethod
    async def get_context(cache_key: str,
                          agent_type: AgentType,
                          cache_db: CacheDatabase) -> list[str]:
        match agent_type:
            case AgentType.ROUTER | AgentType.TOOLING:
                return await cache_db.retrieve_lst(key=cache_key)
            case _:
                raise ValueError(f'Unsupported agent context type: {agent_type}')

    # Save one serialized turn to the selected agent's context list.
    @staticmethod
    async def store_context(cache_key: str,
                            agent_type: AgentType,
                            cache_value: Any,
                            cache_db: CacheDatabase) -> None:
        match agent_type:
            case AgentType.ROUTER:
                await cache_db.insert_list(
                    key=cache_key,
                    value=json.dumps(cache_value),
                    exp_time=1200,
                )
            case AgentType.TOOLING:
                await cache_db.insert_list(
                    key=cache_key,
                    value=json.dumps(cache_value),
                )
            case _:
                raise ValueError(f'Unsupported agent context type: {agent_type}')
                
    # Resolve the router instructions or the skill for a classified message.
    def get_agent_skill(self,
                        message_type: MessageType | None = None,
                        router: bool = False) -> str:
        skill_key: MessageType | str = 'router' if router else message_type
        if skill_key is None:
            raise AgentConfigurationError('A message classification is required to select a skill.')

        skill_path = self.skill_file_map.get(skill_key)
        if not skill_path:
            skill_name = str(skill_key.value) if isinstance(skill_key, MessageType) else skill_key
            raise AgentConfigurationError(f'No skill file is configured for {skill_name}.')

        return get_skill_content(Path(skill_path))

    #Classify the new customer message before selecting a tooling skill.
    async def run_router_agent(self,
                               router_message: str,
                               agent_name: str = 'router_agent') -> MessageType:
        if not self.routing_agent:
            raise AgentConfigurationError('The routing agent model is not configured.')

        router_skill = self.get_agent_skill(router=True)

        router_agent = Agent(
            name=agent_name,
            instructions=router_skill,
            model=self.routing_agent,
            output_type=RouterOutput,
        )

        agent_result = await Runner.run(router_agent, router_message)
        return agent_result.final_output.message_type

    #Run the selected skill with the customer's conversation context.
    async def run_tooling_agent(self,
                                agent_message: AgentMessage,
                                agent_name: str = 'tooling_agent') -> str:
        if not self.tooling_agent:
            raise AgentConfigurationError('The tooling agent model is not configured.')

        agent_skill = self.get_agent_skill(message_type=agent_message.message_type)

        tooling_agent = Agent(
            name=agent_name,
            model=self.tooling_agent,
            instructions=agent_skill,
            tools=self.agent_tool_lst,
            output_type=AgentOutput,
        )

        result = await Runner.run(tooling_agent, agent_message.message)
        return result.final_output.response