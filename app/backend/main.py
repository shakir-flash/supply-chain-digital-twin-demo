from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import text

from analytics.kpi import load_kpis
from model.run_pipeline import run_full, run_scenario
from db.database import refresh_from_csvs, get_engine
from nlp.router import route as route_intent
from analytics.answer_engine_sql import handle as sql_handle

app = FastAPI(title="Supply Chain Digital Twin")

# ---------------- Models ----------------
class Scenario(BaseModel):
    dc_capacity_mult: Dict[str, float] = {}
    region_demand_mult: Dict[str, float] = {}

class Query(BaseModel):
    question: str

class SqlRun(BaseModel):
    query: str
    max_rows: int | None = 5000

# ---------------- App startup ----------------
@app.on_event("startup")
def _startup_refresh():
    try:
        refresh_from_csvs()
    except Exception:
        pass

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

# ---------------- Dashboard helpers ----------------
def safe_query(q: str, params: dict = None):
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

@app.get("/dashboard/summary")
def dashboard_summary():
    """
    Executive summary stats used for hero bar & tiles (no slow lanes).
    """
    engine = get_engine()
    out: Dict[str, Any] = {}
    try:
        df_util = pd.read_sql(text("SELECT utilization_pct FROM dc_utilization"), engine)
        out["avg_dc_utilization_pct"] = float(df_util["utilization_pct"].mean()) if not df_util.empty else 0.0
        out["num_dc_over_80"] = int((df_util["utilization_pct"] >= 80).sum()) if not df_util.empty else 0
        out["num_dc_over_90"] = int((df_util["utilization_pct"] >= 90).sum()) if not df_util.empty else 0
    except Exception:
        out.update({"avg_dc_utilization_pct": 0.0, "num_dc_over_80": 0, "num_dc_over_90": 0})

    try:
        df_region = pd.read_sql(text("SELECT region, flow_cost_usd FROM cost_by_region"), engine)
        total = float(df_region["flow_cost_usd"].sum()) if not df_region.empty else 0.0
        if total > 0 and not df_region.empty:
            row = df_region.sort_values("flow_cost_usd", ascending=False).iloc[0]
            out["top_region"] = str(row["region"])
            out["top_region_cost_share_pct"] = float(100 * row["flow_cost_usd"] / total)
        else:
            out["top_region"] = ""
            out["top_region_cost_share_pct"] = 0.0
    except Exception:
        out["top_region"] = ""
        out["top_region_cost_share_pct"] = 0.0

    try:
        # Active lanes = nonzero volume in optimal_flows
        df_flows = pd.read_sql(text("SELECT COUNT(*) AS c FROM optimal_flows WHERE units_assigned > 0"), engine)
        out["active_lanes"] = int(df_flows["c"].iloc[0]) if not df_flows.empty else 0
    except Exception:
        out["active_lanes"] = 0

    # total cost
    try:
        kpi = load_kpis()
        out["total_cost_with_penalty_usd"] = float(kpi.get("total_cost_with_penalty_usd", 0))
        out["total_transport_cost_usd"] = float(kpi.get("total_transport_cost_usd", 0))
    except Exception:
        out["total_cost_with_penalty_usd"] = 0.0
        out["total_transport_cost_usd"] = 0.0
    return out

@app.get("/dashboard/data_quality")
def data_quality():
    """
    Lightweight data quality signals for the banner.
    """
    engine = get_engine()
    def val(sql: str) -> int:
        try:
            df = pd.read_sql(text(sql), engine)
            return int(df.iloc[0,0]) if not df.empty else 0
        except Exception:
            return 0

    missing_dc_geo = val("SELECT COUNT(*) FROM dcs_clean WHERE lat IS NULL OR lon IS NULL")
    missing_store_geo = val("SELECT COUNT(*) FROM stores_clean WHERE lat IS NULL OR lon IS NULL")
    neg_cost = val("SELECT COUNT(*) FROM transport_clean WHERE cost_per_unit_usd < 0")
    zero_capacity = val("SELECT COUNT(*) FROM dcs_clean WHERE weekly_capacity <= 0")
    orphan_flows = val("""
        SELECT COUNT(*) FROM optimal_flows f
        LEFT JOIN dcs_clean d ON d.dc_id = f.dc_id
        LEFT JOIN stores_clean s ON s.store_id = f.store_id
        WHERE d.dc_id IS NULL OR s.store_id IS NULL
    """)
    return {
        "missing_dc_geo": missing_dc_geo,
        "missing_store_geo": missing_store_geo,
        "negative_cost_rows": neg_cost,
        "zero_capacity_dcs": zero_capacity,
        "orphan_flows": orphan_flows
    }

@app.get("/map/top_lanes")
def map_top_lanes(by: str = "units", n: int = 40):
    """
    Pre-aggregated top-N lanes for the network map.
    by = "units" or "cost"
    """
    metric = "units_assigned" if by.lower() != "cost" else "flow_cost_usd"
    q = f"""
        SELECT f.dc_id, f.store_id, f.units_assigned, f.flow_cost_usd,
               d.lat AS dc_lat, d.lon AS dc_lon, s.lat AS store_lat, s.lon AS store_lon
        FROM optimal_flows f
        JOIN dcs_clean d ON d.dc_id = f.dc_id
        JOIN stores_clean s ON s.store_id = f.store_id
        WHERE f.units_assigned > 0
        ORDER BY f.{metric} DESC
        LIMIT :n
    """
    return safe_query(q, {"n": n})

# ---------------- NLQ (Deterministic SQL) ----------------
@app.post("/nlq")
def api_nlq(q: Query):
    intent = route_intent(q.question)
    if not intent:
        return {
            "mode": "none",
            "answer": "I don’t recognize that question yet. Try asking about utilization, costs, or stores served."
        }
    ans = sql_handle(intent)
    ans["mode"] = "deterministic_sql"
    ans["intent"] = intent
    return ans

# ---------------- Secure SQL Explorer ----------------
DENYLIST = ("insert", "update", "delete", "drop", "alter", "create", "truncate", "attach", "pragma")

def _is_select_only(q: str) -> bool:
    ql = " ".join(q.strip().lower().split())
    if any(tok in ql for tok in DENYLIST):
        return False
    return ql.startswith("select") or ql.startswith("with")

def _sanitize_single_statement(q: str) -> str:
    q_clean = q.strip().rstrip(";").strip()
    if ";" in q_clean:
        raise HTTPException(status_code=400, detail="Only a single statement is allowed. Remove extra ';'.")
    return q_clean

@app.post("/sql/run")
def sql_run(body: SqlRun):
    if not _is_select_only(body.query):
        raise HTTPException(status_code=400, detail="Only read-only SELECT/CTE queries are allowed.")
    q_clean = _sanitize_single_statement(body.query)
    q_to_run = q_clean
    if body.max_rows and "limit" not in q_clean.lower():
        q_to_run = f"SELECT * FROM ({q_clean}) AS t LIMIT {int(body.max_rows)}"
    try:
        df = pd.read_sql(text(q_to_run), get_engine())
        return {
            "columns": list(df.columns),
            "records": df.to_dict(orient="records"),
            "rowcount": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
