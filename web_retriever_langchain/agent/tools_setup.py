from typing import cast, List
from langchain_community.tools import (
    DuckDuckGoSearchRun,
)
from langchain_community.tools.playwright import (
    NavigateTool,
    ClickTool,
    ExtractTextTool,
)
from langchain.tools.base import Tool
from langchain_openai import ChatOpenAI

# --- Link Discovery Tools ---
def get_link_discovery_tools() -> List[Tool]:
    return cast(List[Tool], [NavigateTool(), ExtractTextTool()])


# --- Interactive Browsing Tools ---
def get_interactive_browser_tools() -> List[Tool]:
    return cast(List[Tool], [NavigateTool(), ClickTool(), ExtractTextTool()])


# --- DuckDuckGo + Browser Tools ---
def get_search_browser_tools() -> List[Tool]:
    return cast(List[Tool], [DuckDuckGoSearchRun(), NavigateTool(), ExtractTextTool()])


# --- Generic Combo ---
def get_generic_browser_tools() -> List[Tool]:
    return cast(List[Tool], [NavigateTool(), ClickTool(), ExtractTextTool()])


# --- Dispatcher ---
def get_browser_tools(mode: str = "generic") -> list[Tool]:
    if mode == "generic":
        return get_generic_browser_tools()
    elif mode == "discovery":
        return get_link_discovery_tools()
    elif mode == "interactive":
        return get_interactive_browser_tools()
    elif mode == "search":
        return get_search_browser_tools()
    else:
        raise ValueError(f"Unknown browser tool mode: {mode}")
