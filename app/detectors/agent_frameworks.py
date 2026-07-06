"""Agent framework detection.

Modelled on LLMShadow's `_FRAMEWORK_PATTERNS` (`llm_providers.py`) but expanded
to cover agentic frameworks: LangChain/LangGraph, CrewAI, AutoGPT, AutoGen,
OpenAI Assistants, LlamaIndex, Microsoft Semantic Kernel, and Haystack.

Each match yields a `FrameworkHit`. The repo scanner groups hits per file into
candidate agents and feeds the surrounding evidence into the scoring pipeline.
"""

import re
from dataclasses import dataclass, field
from typing import NamedTuple


class _FrameworkPattern(NamedTuple):
    framework: str
    pattern_name: str
    regex: re.Pattern[str]


# Import / construction patterns per framework. Kept intentionally simple and
# high-signal (mirrors LLMShadow's import-based detection style).
_PATTERNS: list[_FrameworkPattern] = [
    # LangChain / LangGraph
    _FrameworkPattern("langchain", "import langchain", re.compile(r"\b(?:import\s+langchain|from\s+langchain(?:_\w+)?\s+import)\b", re.I)),
    _FrameworkPattern("langchain", "AgentExecutor", re.compile(r"\bAgentExecutor\s*\(", re.I)),
    _FrameworkPattern("langchain", "initialize_agent", re.compile(r"\binitialize_agent\s*\(", re.I)),
    _FrameworkPattern("langgraph", "import langgraph", re.compile(r"\b(?:import\s+langgraph|from\s+langgraph(?:\.\w+)?\s+import)\b", re.I)),
    _FrameworkPattern("langgraph", "StateGraph", re.compile(r"\bStateGraph\s*\(", re.I)),
    # CrewAI
    _FrameworkPattern("crewai", "import crewai", re.compile(r"\b(?:import\s+crewai|from\s+crewai\s+import)\b", re.I)),
    _FrameworkPattern("crewai", "Crew()", re.compile(r"\bCrew\s*\(", re.I)),
    _FrameworkPattern("crewai", "Agent(role=", re.compile(r"\bAgent\s*\(\s*role\s*=", re.I)),
    # AutoGPT
    _FrameworkPattern("autogpt", "import autogpt", re.compile(r"\b(?:import\s+autogpt|from\s+autogpt\s+import)\b", re.I)),
    _FrameworkPattern("autogpt", "AutoGPT(", re.compile(r"\bAuto\s*GPT\s*\(", re.I)),
    # Microsoft AutoGen
    _FrameworkPattern("autogen", "import autogen", re.compile(r"\b(?:import\s+autogen|from\s+autogen(?:_\w+)?\s+import)\b", re.I)),
    _FrameworkPattern("autogen", "AssistantAgent", re.compile(r"\bAssistantAgent\s*\(", re.I)),
    _FrameworkPattern("autogen", "ConversableAgent", re.compile(r"\bConversableAgent\s*\(", re.I)),
    # OpenAI Assistants API
    _FrameworkPattern("openai_assistants", "assistants.create", re.compile(r"\bclient\.beta\.assistants\.create\s*\(", re.I)),
    _FrameworkPattern("openai_assistants", "beta.assistants", re.compile(r"\bbeta\.assistants\b", re.I)),
    # LlamaIndex
    _FrameworkPattern("llama_index", "import llama_index", re.compile(r"\b(?:import\s+llama_index|from\s+llama_index(?:\.\w+)?\s+import)\b", re.I)),
    _FrameworkPattern("llama_index", "ReActAgent", re.compile(r"\bReActAgent\b", re.I)),
    # Microsoft Semantic Kernel
    _FrameworkPattern("semantic_kernel", "import semantic_kernel", re.compile(r"\b(?:import\s+semantic_kernel|from\s+semantic_kernel(?:\.\w+)?\s+import)\b", re.I)),
    # Haystack agents
    _FrameworkPattern("haystack", "import haystack", re.compile(r"\b(?:import\s+haystack|from\s+haystack(?:\.\w+)?\s+import)\b", re.I)),
]

# Package names recognised in dependency manifests (mirrors LLMShadow's
# KNOWN_LLM_PACKAGES approach for manifest-based detection).
KNOWN_AGENT_PACKAGES: dict[str, str] = {
    "langchain": "langchain",
    "langchain-core": "langchain",
    "langchain-community": "langchain",
    "langgraph": "langgraph",
    "crewai": "crewai",
    "autogpt": "autogpt",
    "agpt": "autogpt",
    "pyautogen": "autogen",
    "autogen-agentchat": "autogen",
    "llama-index": "llama_index",
    "llama-index-core": "llama_index",
    "semantic-kernel": "semantic_kernel",
    "farm-haystack": "haystack",
    "haystack-ai": "haystack",
}

# Tool / capability signals used to estimate autonomy and surface tool usage.
_TOOL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("shell_exec", re.compile(r"\b(?:subprocess|os\.system|ShellTool|PythonREPL|exec\s*\()\b", re.I)),
    ("filesystem", re.compile(r"\b(?:open\s*\(|FileManagementToolkit|ReadFileTool|WriteFileTool)\b", re.I)),
    ("http_request", re.compile(r"\b(?:requests\.(?:get|post)|httpx\.|RequestsToolkit|aiohttp)\b", re.I)),
    ("web_search", re.compile(r"\b(?:SerpAPI|TavilySearch|DuckDuckGo|GoogleSearch|web_search)\b", re.I)),
    ("database", re.compile(r"\b(?:SQLDatabase|sqlalchemy|psycopg2|execute\s*\(\s*[\"'](?:SELECT|INSERT|UPDATE|DELETE))\b", re.I)),
    ("code_interpreter", re.compile(r"\b(?:code_interpreter|PythonAstREPLTool|PythonREPLTool)\b", re.I)),
    ("email", re.compile(r"\b(?:smtplib|GmailToolkit|send_email)\b", re.I)),
]

# Tools generally treated as high blast-radius for autonomy estimation.
_HIGH_RISK_TOOLS = {"shell_exec", "code_interpreter", "database", "filesystem"}


@dataclass
class FrameworkHit:
    framework: str
    pattern_name: str
    evidence: str
    line: int


@dataclass
class FileDetection:
    """All agent-relevant signals found in a single source file."""

    file_path: str
    frameworks: set[str] = field(default_factory=set)
    hits: list[FrameworkHit] = field(default_factory=list)
    tools: set[str] = field(default_factory=set)

    @property
    def is_agent(self) -> bool:
        return bool(self.frameworks)


_EVIDENCE_CTX = 50


def _evidence(text: str, start: int, end: int) -> str:
    a = max(0, start - _EVIDENCE_CTX)
    b = min(len(text), end + _EVIDENCE_CTX)
    return ("..." if a > 0 else "") + text[a:b].replace("\n", " ").strip() + ("..." if b < len(text) else "")


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def detect_file(file_path: str, content: str) -> FileDetection:
    """Scan a single file's text content for agent frameworks and tools."""
    detection = FileDetection(file_path=file_path)
    for pat in _PATTERNS:
        for match in pat.regex.finditer(content):
            detection.frameworks.add(pat.framework)
            detection.hits.append(
                FrameworkHit(
                    framework=pat.framework,
                    pattern_name=pat.pattern_name,
                    evidence=_evidence(content, match.start(), match.end()),
                    line=_line_of(content, match.start()),
                )
            )
    if detection.frameworks:
        for tool_name, regex in _TOOL_PATTERNS:
            if regex.search(content):
                detection.tools.add(tool_name)
    return detection


def estimate_autonomy(tools: set[str]) -> str:
    """Heuristic autonomy level from the breadth/danger of available tools."""
    high = len(tools & _HIGH_RISK_TOOLS)
    if high >= 2 or (high >= 1 and len(tools) >= 3):
        return "high"
    if tools:
        return "medium"
    return "low"
