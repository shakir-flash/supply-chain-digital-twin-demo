# db/database.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CLEAN_DIR = DATA_DIR / "clean"
RESULTS_DIR = DATA_DIR / "results"
DB_PATH = DATA_DIR / "warehouse.db"

_engine = None  # module-level cache

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
    return _engine

def _to_sql(df: pd.DataFrame, name: str):
    eng = get_engine()
    df.to_sql(name, eng, if_exists="replace", index=False)

def refresh_from_csvs():
    """(Re)load CSV outputs into SQLite warehouse. Call after pipeline/scenario."""
    # Minimal required tables for dashboard/NLQ
    files = {
        "kpi_summary": RESULTS_DIR / "kpi_summary.csv",
        "dc_utilization": RESULTS_DIR / "dc_utilization.csv",
        "optimal_flows": RESULTS_DIR / "optimal_flows.csv",
        "cost_by_dc": RESULTS_DIR / "cost_by_dc.csv",
        "cost_by_region": RESULTS_DIR / "cost_by_region.csv",
        "slow_lanes_detail": RESULTS_DIR / "slow_lanes_detail.csv",
        "unmet_demand": RESULTS_DIR / "unmet_demand.csv",
        # reference
        "stores_clean": CLEAN_DIR / "stores_clean.csv",
        "dcs_clean": CLEAN_DIR / "dcs_clean.csv",
        "transport_clean": CLEAN_DIR / "transport_clean.csv",
    }
    for name, path in files.items():
        if path.exists():
            _to_sql(pd.read_csv(path), name)

    _create_indexes_and_views()

def _create_indexes_and_views():
    eng = get_engine()
    with eng.begin() as con:
        # indexes for faster queries
        for tbl, cols in [
            ("dc_utilization", ["dc_id"]),
            ("optimal_flows", ["dc_id", "store_id"]),
            ("stores_clean", ["store_id", "region"]),
            ("cost_by_dc", ["dc_id"]),
            ("transport_clean", ["dc_id", "store_id"]),
        ]:
            for c in cols:
                con.exec_driver_sql(f"CREATE INDEX IF NOT EXISTS ix_{tbl}_{c} ON {tbl}({c});")

        # sample view: flows with geo + service time
        con.exec_driver_sql("""
        CREATE VIEW IF NOT EXISTS v_flows_enriched AS
        SELECT f.dc_id, f.store_id, f.units_assigned, f.flow_cost_usd, f.cost_per_unit_usd,
               d.lat AS dc_lat, d.lon AS dc_lon,
               s.lat AS st_lat, s.lon AS st_lon, s.region,
               t.service_time_days
        FROM optimal_flows f
        LEFT JOIN dcs_clean d ON f.dc_id = d.dc_id
        LEFT JOIN stores_clean s ON f.store_id = s.store_id
        LEFT JOIN transport_clean t ON f.dc_id = t.dc_id AND f.store_id = t.store_id;
        """)
