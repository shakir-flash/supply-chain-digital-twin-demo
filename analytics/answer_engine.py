# analytics/answer_engine.py
from __future__ import annotations
import pandas as pd
from functools import lru_cache
from typing import Dict, Any
from config import RESULTS_DIR, CLEAN_DIR

# ---------- fast cached loaders ----------
@lru_cache(maxsize=16)
def _kpi_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "kpi_summary.csv")

@lru_cache(maxsize=16)
def _util_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "dc_utilization.csv")

@lru_cache(maxsize=16)
def _flows_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "optimal_flows.csv")

@lru_cache(maxsize=16)
def _slow_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "slow_lanes_detail.csv")

@lru_cache(maxsize=16)
def _region_cost_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "cost_by_region.csv")

@lru_cache(maxsize=16)
def _dc_cost_df() -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / "cost_by_dc.csv")

@lru_cache(maxsize=16)
def _stores_df() -> pd.DataFrame:
    return pd.read_csv(CLEAN_DIR / "stores_clean.csv")

# Clear caches (call when scenario/pipeline re-runs)
def reset_caches():
    _kpi_df.cache_clear()
    _util_df.cache_clear()
    _flows_df.cache_clear()
    _slow_df.cache_clear()
    _region_cost_df.cache_clear()
    _dc_cost_df.cache_clear()
    _stores_df.cache_clear()

# ---------- helpers ----------
def _kpi_val(metric: str, default=0.0) -> float:
    df = _kpi_df()
    row = df.loc[df["metric"] == metric]
    if row.empty:
        return float(default)
    try:
        return float(row.iloc[0]["value"])
    except Exception:
        return float(default)

def fmt_usd(x: float) -> str:
    return f"${x:,.0f}"

def fmt_pct(x: float, p: int = 1) -> str:
    return f"{x:.{p}f}%"

# ---------- intent handlers ----------
def total_cost(_: Dict[str, Any]) -> Dict[str, Any]:
    val = _kpi_val("total_cost_with_penalty_usd")
    return {
        "answer": f"Total cost (incl. penalty): {fmt_usd(val)}.",
        "source": "kpi_summary.csv: total_cost_with_penalty_usd",
        "metrics": {"total_cost_with_penalty_usd": val},
    }

def transport_cost(_: Dict[str, Any]) -> Dict[str, Any]:
    val = _kpi_val("total_transport_cost_usd")
    return {
        "answer": f"Transport cost: {fmt_usd(val)}.",
        "source": "kpi_summary.csv: total_transport_cost_usd",
        "metrics": {"total_transport_cost_usd": val},
    }

def unmet_units(_: Dict[str, Any]) -> Dict[str, Any]:
    val = _kpi_val("unmet_penalty_usd", 0.0)  # keep penalty for context
    # add units explicitly from unmet_demand.csv (already merged in build)
    try:
        unmet = pd.read_csv(RESULTS_DIR / "unmet_demand.csv")["unmet_units"].sum()
    except Exception:
        unmet = 0.0
    return {
        "answer": f"Unmet demand: {unmet:,.0f} units (penalty {fmt_usd(val)}).",
        "source": "unmet_demand.csv, kpi_summary.csv",
        "metrics": {"unmet_units": float(unmet), "unmet_penalty_usd": float(val)},
    }

def highest_util_dc(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _util_df().sort_values("utilization_pct", ascending=False)
    row = df.iloc[0]
    return {
        "answer": f"Highest utilization: {row['dc_id']} at {row['utilization_pct']:.1f}% (assigned {row['units_assigned']:,.0f} / cap {row['weekly_capacity']:,.0f}).",
        "source": "dc_utilization.csv",
        "metrics": {"dc_id": row["dc_id"], "utilization_pct": float(row["utilization_pct"])},
    }

def lowest_util_dc(_: Dict[str, Any]) -> Dict[str, Any]:
    df = _util_df().sort_values("utilization_pct", ascending=True)
    row = df.iloc[0]
    return {
        "answer": f"Lowest utilization: {row['dc_id']} at {row['utilization_pct']:.1f}%.",
        "source": "dc_utilization.csv",
        "metrics": {"dc_id": row["dc_id"], "utilization_pct": float(row["utilization_pct"])},
    }

def dc_util(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id", "")
    df = _util_df()
    sub = df.loc[df["dc_id"] == dc]
    if sub.empty:
        return {"answer": f"I can’t find DC '{dc}'.", "source": "dc_utilization.csv", "metrics": {}}
    row = sub.iloc[0]
    return {
        "answer": f"{dc} utilization: {row['utilization_pct']:.1f}% (assigned {row['units_assigned']:,.0f} / cap {row['weekly_capacity']:,.0f}).",
        "source": "dc_utilization.csv",
        "metrics": {"dc_id": dc, "utilization_pct": float(row["utilization_pct"])},
    }

def cost_by_region(args: Dict[str, Any]) -> Dict[str, Any]:
    order = args.get("order", "desc")
    top = int(args.get("top", 3))
    asc = order == "asc"
    df = _region_cost_df().sort_values("flow_cost_usd", ascending=asc).head(top)
    pairs = [f"{r.region}: {fmt_usd(r.flow_cost_usd)}" for r in df.itertuples(index=False)]
    hdr = "Lowest" if asc else "Highest"
    return {
        "answer": f"{hdr} regional transport cost: " + "; ".join(pairs) + ".",
        "source": "cost_by_region.csv",
        "metrics": {"order": order, "top": top},
    }

def cost_by_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    order = args.get("order", "desc")
    top = int(args.get("top", 5))
    asc = order == "asc"
    df = _dc_cost_df().sort_values("flow_cost_usd", ascending=asc).head(top)
    pairs = [f"{r.dc_id}: {fmt_usd(r.flow_cost_usd)}" for r in df.itertuples(index=False)]
    hdr = "Lowest" if asc else "Highest"
    return {
        "answer": f"{hdr} DC transport cost: " + "; ".join(pairs) + ".",
        "source": "cost_by_dc.csv",
        "metrics": {"order": order, "top": top},
    }

def slow_lanes(args: Dict[str, Any]) -> Dict[str, Any]:
    top = int(args.get("top", 5))
    df = _slow_df().copy()
    if df.empty:
        return {"answer": "No slow lanes (>2 days) in current solution.", "source": "slow_lanes_detail.csv", "metrics": {}}
    # Sort by units or service time (choose units for impact)
    lanes = df.sort_values("units_assigned", ascending=False).head(top)
    items = [f"{r.dc_id}->{r.store_id} ({r.service_time_days:.1f}d, {int(r.units_assigned):,}u)" for r in lanes.itertuples(index=False)]
    return {
        "answer": "Top slow lanes: " + "; ".join(items) + ".",
        "source": "slow_lanes_detail.csv",
        "metrics": {"top": top},
    }

def stores_served_by_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id", "")
    df = _flows_df()
    if df.empty:
        return {"answer": "No flow data.", "source": "optimal_flows.csv", "metrics": {}}
    cnt = df.loc[df["dc_id"] == dc, "store_id"].nunique()
    return {"answer": f"{dc} serves {cnt} store(s).", "source": "optimal_flows.csv", "metrics": {"dc_id": dc, "stores_served": int(cnt)}}

def stores_for_dc(args: Dict[str, Any]) -> Dict[str, Any]:
    dc = args.get("dc_id", "")
    top = int(args.get("top", 20))
    df = _flows_df().loc[_flows_df()["dc_id"] == dc].sort_values("units_assigned", ascending=False).head(top)
    if df.empty:
        return {"answer": f"No stores found for {dc}.", "source": "optimal_flows.csv", "metrics": {}}
    items = [f"{r.store_id} ({int(r.units_assigned):,}u)" for r in df.itertuples(index=False)]
    return {"answer": f"Top stores for {dc}: " + "; ".join(items) + ".", "source": "optimal_flows.csv", "metrics": {"dc_id": dc, "top": top}}

# Intent dispatcher
_DISPATCH = {
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
    fn = _DISPATCH.get(intent["name"])
    if not fn:
        return {"answer": "Sorry, I don't have a deterministic handler for that yet.", "source": "", "metrics": {}}
    return fn(intent.get("args", {}))
