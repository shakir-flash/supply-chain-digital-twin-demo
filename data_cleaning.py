# data_cleaning.py
# Cleans, validates, and prepares model-ready tables. Exports a one-row Data Quality Report.

import pandas as pd
import numpy as np

from config import RAW_DIR, CLEAN_DIR
from collections import OrderedDict

def load_raw():
    dcs = pd.read_csv(RAW_DIR / "dcs_raw.csv")
    stores = pd.read_csv(RAW_DIR / "stores_raw.csv")
    transport = pd.read_csv(RAW_DIR / "transport_raw.csv")
    return dcs, stores, transport

def clean_tables(dcs_raw: pd.DataFrame, stores_raw: pd.DataFrame, transport_raw: pd.DataFrame):
    # Standardize IDs
    dcs = dcs_raw.copy()
    stores = stores_raw.copy()
    transport = transport_raw.copy()

    for col in ["dc_id"]:
        dcs[col] = dcs[col].astype(str).str.strip().str.upper()
    for col in ["store_id"]:
        stores[col] = stores[col].astype(str).str.strip().str.upper()
    for col in ["dc_id", "store_id"]:
        transport[col] = transport[col].astype(str).str.strip().str.upper()

    # Deduplicate
    dcs = dcs.drop_duplicates()
    stores = stores.drop_duplicates()
    transport = transport.drop_duplicates()

    # Impute regions using mode
    if "region" in stores.columns:
        region_mode = stores["region"].mode().iat[0] if not stores["region"].dropna().empty else "Unknown"
        stores["region"] = stores["region"].fillna(region_mode)

    # Coerce numerics
    for col in ["weekly_capacity", "fixed_cost_usd_wk"]:
        if col in dcs.columns:
            dcs[col] = pd.to_numeric(dcs[col], errors="coerce")
    for col in ["weekly_demand", "lat", "lon"]:
        if col in stores.columns:
            stores[col] = pd.to_numeric(stores[col], errors="coerce")
    for col in ["distance_mi", "cost_per_unit_usd", "service_time_days"]:
        if col in transport.columns:
            transport[col] = pd.to_numeric(transport[col], errors="coerce")

    # Impute missing capacity with median
    if "weekly_capacity" in dcs.columns:
        cap_med = int(dcs["weekly_capacity"].median())
        dcs["weekly_capacity"] = dcs["weekly_capacity"].fillna(cap_med).astype(int)

    # Impute missing demand using region median
    if "weekly_demand" in stores.columns:
        med_by_region = stores.groupby("region")["weekly_demand"].median().to_dict()
        stores["weekly_demand"] = stores.apply(
            lambda r: med_by_region.get(r["region"], stores["weekly_demand"].median()) if pd.isna(r["weekly_demand"]) else r["weekly_demand"],
            axis=1
        ).round().astype(int)

    # Referential integrity for transport
    transport = transport.merge(dcs[["dc_id"]], on="dc_id", how="inner")
    transport = transport.merge(stores[["store_id"]], on="store_id", how="inner")

    # Aggregate any duplicate dc-store pairs
    transport = transport.groupby(["dc_id", "store_id"], as_index=False).agg({
        "distance_mi": "mean",
        "cost_per_unit_usd": "mean",
        "service_time_days": "mean"
    })

    return dcs, stores, transport

def data_quality_report(dcs: pd.DataFrame, stores: pd.DataFrame, transport: pd.DataFrame):
    rep = OrderedDict()
    rep["stores_rows"] = len(stores)
    rep["dcs_rows"] = len(dcs)
    rep["transport_rows"] = len(transport)
    rep["total_weekly_demand"] = int(stores["weekly_demand"].sum())
    rep["total_dc_capacity"] = int(dcs["weekly_capacity"].sum())
    rep["capacity_minus_demand"] = int(dcs["weekly_capacity"].sum() - stores["weekly_demand"].sum())
    return pd.DataFrame([rep])

def run():
    dcs_raw, stores_raw, transport_raw = load_raw()
    dcs_clean, stores_clean, transport_clean = clean_tables(dcs_raw, stores_raw, transport_raw)
    dcs_clean.to_csv(CLEAN_DIR / "dcs_clean.csv", index=False)
    stores_clean.to_csv(CLEAN_DIR / "stores_clean.csv", index=False)
    transport_clean.to_csv(CLEAN_DIR / "transport_clean.csv", index=False)
    dq = data_quality_report(dcs_clean, stores_clean, transport_clean)
    dq.to_csv(CLEAN_DIR / "data_quality_report.csv", index=False)

if __name__ == "__main__":
    run()
