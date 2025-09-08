# analytics/answer_engine_sql.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
from sqlalchemy import text
from db.database import get_engine

def _read_sql(q: str, params: Dict[str, Any] | None = None) -> pd.DataFrame:
    eng = get_engine()
    return pd.read_sql(text(q), eng, params=params or {})

def fmt_usd(x: float) -> str:
    return f"${x:,.0f}"

def total_cost(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _read_sql("SELECT value FROM kpi_summary WHERE metric='total_cost_with_penalty_usd' LIMIT 1;")
    val = float(df.iloc[0]["value"]) if not df.empty else 0.0
    return {"answer": f"Total cost (incl. penalty): {fmt_usd(val)}.", "source": "kpi_summary.total_cost_with_penalty_usd"}

def transport_cost(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _read_sql("SELECT value FROM kpi_summary WHERE metric='total_transport_cost_usd' LIMIT 1;")
    val = float(df.iloc[0]["value"]) if not df.empty else 0.0
    return {"answer": f"Transport cost: {fmt_usd(val)}.", "source": "kpi_summary.total_transport_cost_usd"}

def unmet_units(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _read_sql("SELECT SUM(unmet_units) AS u FROM unmet_demand;")
    u = float(df.iloc[0]["u"]) if not df.empty and df.iloc[0]["u"] is not None else 0.0
    pen = _read_sql("SELECT value FROM kpi_summary WHERE metric='unmet_penalty_usd' LIMIT 1;")
    p = float(pen.iloc[0]["value"]) if not pen.empty else 0.0
    return {"answer": f"Unmet demand: {u:,.0f} units (penalty {fmt_usd(p)}).", "source": "unmet_demand, kpi_summary"}

def highest_util_dc(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _read_sql("""
        SELECT dc_id, utilization_pct, units_assigned, weekly_capacity
        FROM dc_utilization
        ORDER BY utilization_pct DESC, dc_id ASC LIMIT 1;
    """)
    if df.empty: return {"answer":"No utilization data.","source":"dc_utilization"}
    r = df.iloc[0]
    return {"answer": f"Highest utilization: {r.dc_id} at {float(r.utilization_pct):.1f}% (assigned {int(r.units_assigned):,} / cap {int(r.weekly_capacity):,}).",
            "source":"dc_utilization"}

def lowest_util_dc(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _read_sql("""
        SELECT dc_id, utilization_pct FROM dc_utilization
        ORDER BY utilization_pct ASC, dc_id ASC LIMIT 1;
    """)
    if df.empty: return {"answer":"No utilization data.","source":"dc_utilization"}
    r = df.iloc[0]
    return {"answer": f"Lowest utilization: {r.dc_id} at {float(r.utilization_pct):.1f}%.", "source":"dc_utilization"}

def dc_util(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id","")
    df = _read_sql("""
        SELECT dc_id, utilization_pct, units_assigned, weekly_capacity
        FROM dc_utilization WHERE dc_id=:dc LIMIT 1;
    """, {"dc": dc})
    if df.empty: return {"answer": f"I can’t find DC '{dc}'.","source":"dc_utilization"}
    r = df.iloc[0]
    return {"answer": f"{r.dc_id} utilization: {float(r.utilization_pct):.1f}% (assigned {int(r.units_assigned):,} / cap {int(r.weekly_capacity):,}).",
            "source":"dc_utilization"}

def cost_by_region(args: Dict[str, Any]) -> Dict[str, Any]:
    order = "ASC" if args.get("order") == "asc" else "DESC"
    top = int(args.get("top", 3))
    df = _read_sql(f"""
        SELECT region, flow_cost_usd FROM cost_by_region
        ORDER BY flow_cost_usd {order} LIMIT :n;
    """, {"n": top})
    if df.empty: return {"answer":"No regional cost data.","source":"cost_by_region"}
    parts = [f"{r.region}: {fmt_usd(float(r.flow_cost_usd))}" for _, r in df.iterrows()]
    hdr = "Lowest" if order=="ASC" else "Highest"
    return {"answer": f"{hdr} regional transport cost: " + "; ".join(parts) + ".", "source":"cost_by_region"}

def cost_by_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    order = "ASC" if args.get("order") == "asc" else "DESC"
    top = int(args.get("top", 5))
    df = _read_sql(f"""
        SELECT dc_id, flow_cost_usd FROM cost_by_dc
        ORDER BY flow_cost_usd {order} LIMIT :n;
    """, {"n": top})
    if df.empty: return {"answer":"No DC cost data.","source":"cost_by_dc"}
    parts = [f"{r.dc_id}: {fmt_usd(float(r.flow_cost_usd))}" for _, r in df.iterrows()]
    hdr = "Lowest" if order=="ASC" else "Highest"
    return {"answer": f"{hdr} DC transport cost: " + "; ".join(parts) + ".", "source":"cost_by_dc"}

def slow_lanes(args: Dict[str, Any]) -> Dict[str, Any]:
    top = int(args.get("top", 5))
    df = _read_sql("""
        SELECT dc_id, store_id, service_time_days, units_assigned
        FROM slow_lanes_detail
        ORDER BY units_assigned DESC
        LIMIT :n;
    """, {"n": top})
    if df.empty: return {"answer":"No slow lanes (>2 days) in current solution.","source":"slow_lanes_detail"}
    parts = [f"{r.dc_id}->{r.store_id} ({float(r.service_time_days):.1f}d, {int(r.units_assigned):,}u)" for _, r in df.iterrows()]
    return {"answer":"Top slow lanes: " + "; ".join(parts) + ".", "source":"slow_lanes_detail"}

def stores_served_by_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id","")
    df = _read_sql("""
        SELECT COUNT(DISTINCT store_id) AS cnt FROM optimal_flows WHERE dc_id=:dc;
    """, {"dc": dc})
    cnt = int(df.iloc[0]["cnt"]) if not df.empty else 0
    return {"answer": f"{dc} serves {cnt} store(s).", "source":"optimal_flows"}

def stores_for_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id","")
    top = int(args.get("top", 20))
    df = _read_sql("""
        SELECT store_id, units_assigned
        FROM optimal_flows WHERE dc_id=:dc
        ORDER BY units_assigned DESC LIMIT :n;
    """, {"dc": dc, "n": top})
    if df.empty: return {"answer": f"No stores found for {dc}.","source":"optimal_flows"}
    parts = [f"{r.store_id} ({int(r.units_assigned):,}u)" for _, r in df.iterrows()]
    return {"answer": f"Top stores for {dc}: " + "; ".join(parts) + ".", "source":"optimal_flows"}

# dispatcher
DISPATCH = {
    "total_cost": total_cost,
    "transport_cost": transport_cost,
    "unmet_units": unmet_units,
    "highest_util_dc": highest_util_dc,
    "lowest_util_dc": lowest_util_dc,
    "dc_util": dc_util,
    "cost_by_region": cost_by_region,
    "cost_by_dc": cost_by_dc,
    "slow_lanes": slow_lanes,
    "stores_served_by_dc": stores_served_by_dc,
    "stores_for_dc": stores_for_dc,
}

def handle(intent: Dict[str, Any]) -> Dict[str, Any]:
    fn = DISPATCH.get(intent["name"])
    if not fn:
        return {"answer":"No deterministic SQL handler for that question yet.","source":""}
    return fn(intent.get("args", {}))
