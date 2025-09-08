# llm/agent.py
import json
from analytics.kpi import load_kpis
from llm.rag import retrieve_context
from llm.ollama_client import chat_local

def answer_question(q: str) -> str:
    k = load_kpis()
    context = retrieve_context(q)
    prompt = f"""
You are a Supply Chain Network Strategy analyst. Answer concisely with numbers and business implications.
Question: {q}

== Latest KPIs ==
{json.dumps(k, indent=2)}

== Context ==
{context}

If scenario is implied, suggest a lever (capacity or regional demand) and mention expected trade-off (cost vs. service).
"""
    return chat_local(prompt)
