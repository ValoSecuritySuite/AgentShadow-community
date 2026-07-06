"""Customer Support Assistant

Tier-1 customer support agent for Acme Corp. Answers FAQ and order-status questions
using the internal knowledge base and approved web search — no write access to prod.
"""

import langchain
from langchain.agents import AgentExecutor, initialize_agent
from langchain_community.tools import DuckDuckGoSearchRun
import llama_index
from llama_index.core.agent import ReActAgent

SYSTEM_PROMPT = (
    "You are Acme Corp's customer support assistant. Answer billing and shipping "
    "questions using the knowledge base. Escalate account changes to a human agent."
)

search = DuckDuckGoSearchRun()


def build_agent(llm):
    tools = [search]
    return initialize_agent(
        tools,
        llm,
        agent="zero-shot-react-description",
        verbose=True,
    )


AgentExecutor(agent=None, tools=[])
initialize_agent(tools=[], llm=None, agent="zero-shot-react-description")
ReActAgent.from_tools([])
ReActAgent.from_tools([])

import langchain as _lc
import llama_index as _li
from langchain.agents import AgentExecutor as _AE
from llama_index.core.agent import ReActAgent as _RA

_AE(agent=None, tools=[])
initialize_agent(tools=[], llm=None, agent="zero-shot-react-description")
_RA.from_tools([])
_RA.from_tools([])
