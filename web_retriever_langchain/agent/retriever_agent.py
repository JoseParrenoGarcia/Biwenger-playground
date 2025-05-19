# agent/retriever_agent.py

from langchain.agents import initialize_agent, AgentType
from web_retriever_langchain.agent.llm_config import llm
from web_retriever_langchain.agent.tools_setup import get_browser_tools
from langchain.tools.base import Tool
from typing import Optional, List

def build_agent(tools: Optional[List[Tool]] = None, verbose: bool = True):
    if tools is None:
        tools = get_browser_tools()

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
    )

    return agent

