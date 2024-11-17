# agents/solution_templates_agent.py

from crewai import Agent, LLM
from tools.airtable_tool import AirtableTool
import os
import json

def solution_templates_agent_logic(self):
    # Implement the agent logic here
    pass  # Placeholder for actual logic

def get_solution_templates_agent(config, tools, llm):
    agent_conf = config['solution_templates_agent']
    agent_instance = Agent(
        llm=llm,
        tools=tools,
        **agent_conf
    )
    # Assign custom logic to the agent's run method
    agent_instance.run = solution_templates_agent_logic.__get__(agent_instance, Agent)
    return agent_instance
