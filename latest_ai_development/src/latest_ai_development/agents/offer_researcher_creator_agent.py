# agents/offer_creator_agent.py

from crewai import Agent, LLM
from tools.airtable_tool import AirtableTool
import os
import json

def offer_creator_agent_logic(self):
    # Implement the agent logic here
    pass  # Placeholder for actual logic

def get_offer_creator_agent(config, tools, llm):
    agent_conf = config['offer_creator_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = offer_creator_agent_logic.__get__(agent_instance, Agent)
    return agent_instance
