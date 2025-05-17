# agent/tools_setup.py

from langchain_community.tools.playwright import (
    NavigateTool,
    ExtractTextTool,
    ExtractHyperlinksTool,
)

def get_browser_tools():
    tools = [
        NavigateTool(),
        ExtractTextTool(),
        ExtractHyperlinksTool(),
    ]
    return tools
