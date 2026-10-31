"""
Enterprise AI Support Platform
Session 3 of 12 — The ReAct Architecture

Extends Session 2 with full ReAct loop safety:
circuit breaker, context trimming, duplicate detection.
Fraud handler upgraded from stub to real tool calling.

Run server: python api.py  → http://localhost:8000
Run CLI:    python support_agent.py
"""

import os
import time
import operator
import json
import uuid
from typing import TypedDict, Annotated, Literal, Any

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# ── Environment setup ────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or os.environ.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini"

if not OPENROUTER_API_KEY:
    raise EnvironmentError(
        "OPENROUTER_API_KEY or OPENAI_API_KEY not set. Run: export OPENROUTER_API_KEY='your-key-here'"
    )

if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = (
        "https://openrouter.ai/api/v1"
        if os.environ.get("OPENROUTER_API_KEY")
        else "https://api.openai.com/v1"
    )

llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    temperature=0,
)
print(f"[System] OpenAI/OpenRouter model initialized | model={OPENAI_MODEL} | base_url={OPENROUTER_BASE_URL}")

# ── ReAct Constants (Session 3) ─────────────────────────────────────────────
MAX_ITERATIONS    = 5
CONTEXT_THRESHOLD = 12

print(f"[ReAct] MAX_ITERATIONS={MAX_ITERATIONS} | "
      f"CONTEXT_THRESHOLD={CONTEXT_THRESHOLD}")
