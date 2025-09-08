# app/backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text

from analytics.kpi import load_kpis
from model.run_pipeline import run_full, run_scenario
from db.database import refresh_from_csvs, get_engine
from nlp.router import route as route_intent
from analytics.answer_engine_sql import handle as sql_handle

app = FastAPI(title="Supply Chain Digital Twin")

class Scenario(BaseModel):
    dc_capacity_mult: Dict[str, float] = {}
    region_demand_mult: Dict[str, float] = {}

class Query(BaseModel):
    question: str


# ---------------- Health ----------------
@app.get("/health")
def health():
    return {"ok": True}


# ---------------- Pipeline ----------------
@app.post("/run/full")
def api_run_full():
    run_full()
    refresh_from_csvs()
    return load_kpis()

@app.get("/kpi")
def api_kpi():
    return load_kpis()

@app.post("/scenario/run")
def api_scenario_run(s: Scenario):
    run_scenario(s.dict())
    refresh_from_csvs()
    return load_kpis()


# ---------------- Dashboard (SQL-backed) ----------------
def safe_query(q: str, params: dict = None):
    """Helper to wrap dashboard SQL queries safely."""
    try:
        df = pd.read_sql(text(q), get_engine(), params=params or {})
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e), "records": []}

@app.get("/dashboard/util/top")
def util_top(n: int = 10):
    q = """
        SELECT dc_id, utilization_pct
        FROM dc_utilization
        ORDER BY utilization_pct DESC
        LIMIT :n;
    """
    return safe_query(q, {"n": n})

@app.get("/dashboard/cost/by_dc")
def cost_by_dc(n: int = 10, order: str = "desc"):
    order_sql = "DESC" if order.lower() != "asc" else "ASC"
    q = f"""
        SELECT dc_id, flow_cost_usd
        FROM cost_by_dc
        ORDER BY flow_cost_usd {order_sql}
        LIMIT :n;
    """
    return safe_query(q, {"n": n})

@app.get("/dashboard/cost/by_region")
def cost_by_region(n: int = 4, order: str = "desc"):
    order_sql = "DESC" if order.lower() != "asc" else "ASC"
    q = f"""
        SELECT region, flow_cost_usd
        FROM cost_by_region
        ORDER BY flow_cost_usd {order_sql}
        LIMIT :n;
    """
    return safe_query(q, {"n": n})

@app.get("/dashboard/demand/dist")
def demand_dist():
    q = """
        SELECT weekly_demand
        FROM stores_clean
        WHERE weekly_demand IS NOT NULL
    """
    return safe_query(q)



# ---------------- NLQ (Deterministic SQL) ----------------
@app.post("/nlq")
def api_nlq(q: Query):
    intent = route_intent(q.question)
    if not intent:
        return {
            "mode": "none",
            "answer": "I don’t recognize that question yet. Try asking about utilization, costs, slow lanes, or stores served."
        }
    ans = sql_handle(intent)
    ans["mode"] = "deterministic_sql"
    ans["intent"] = intent
    return ans
