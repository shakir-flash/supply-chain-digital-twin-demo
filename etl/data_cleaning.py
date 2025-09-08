# etl/data_cleaning.py
import pandas as pd, numpy as np
from collections import OrderedDict
from config import RAW_DIR, CLEAN_DIR

def load_raw():
    return (pd.read_csv(RAW_DIR/"dcs_raw.csv"),
            pd.read_csv(RAW_DIR/"stores_raw.csv"),
            pd.read_csv(RAW_DIR/"transport_raw.csv"))

def clean_tables(dcs_raw, stores_raw, transport_raw):
    dcs, stores, transport = dcs_raw.copy(), stores_raw.copy(), transport_raw.copy()

    dcs["dc_id"] = dcs["dc_id"].astype(str).str.strip().str.upper()
    stores["store_id"] = stores["store_id"].astype(str).str.strip().str.upper()
    transport["dc_id"] = transport["dc_id"].astype(str).str.strip().str.upper()
    transport["store_id"] = transport["store_id"].astype(str).str.strip().str.upper()

    dcs, stores, transport = dcs.drop_duplicates(), stores.drop_duplicates(), transport.drop_duplicates()

    # Coerce numerics
    for col in ["weekly_capacity","fixed_cost_usd_wk","lat","lon"]:
        if col in dcs.columns: dcs[col] = pd.to_numeric(dcs[col], errors="coerce")
    for col in ["weekly_demand","lat","lon"]:
        if col in stores.columns: stores[col] = pd.to_numeric(stores[col], errors="coerce")
    for col in ["distance_mi","cost_per_unit_usd","service_time_days"]:
        if col in transport.columns: transport[col] = pd.to_numeric(transport[col], errors="coerce")

    # Regions
    if "region" in stores.columns:
        region_mode = stores["region"].dropna().mode().iat[0] if not stores["region"].dropna().empty else "Unknown"
        stores["region"] = stores["region"].fillna(region_mode)

    # Impute capacity/demand
    cap_med = int(dcs["weekly_capacity"].median())
    dcs["weekly_capacity"] = dcs["weekly_capacity"].fillna(cap_med).astype(int)

    med_by_region = stores.groupby("region")["weekly_demand"].median().to_dict()
    stores["weekly_demand"] = stores.apply(
        lambda r: med_by_region.get(r["region"], stores["weekly_demand"].median())
        if pd.isna(r["weekly_demand"]) else r["weekly_demand"], axis=1
    ).round().astype(int)

    # Referential integrity
    transport = transport.merge(dcs[["dc_id"]], on="dc_id", how="inner")
    transport = transport.merge(stores[["store_id"]], on="store_id", how="inner")

    # Aggregate duplicate lane rows
    transport = transport.groupby(["dc_id","store_id"], as_index=False).agg({
        "distance_mi":"mean","cost_per_unit_usd":"mean","service_time_days":"mean"
    })

    return dcs, stores, transport

def data_quality_report(dcs, stores, transport):
    rep = OrderedDict()
    rep["stores_rows"] = len(stores)
    rep["dcs_rows"] = len(dcs)
    rep["transport_rows"] = len(transport)
    rep["total_weekly_demand"] = int(stores["weekly_demand"].sum())
    rep["total_dc_capacity"] = int(dcs["weekly_capacity"].sum())
    rep["capacity_minus_demand"] = rep["total_dc_capacity"] - rep["total_weekly_demand"]
    rep["lane_id_coverage_pct"] = round(100.0*len(transport)/(len(dcs)*len(stores)), 2)
    rep["nonneg_costs_pct"] = round(100.0*(transport["cost_per_unit_usd"]>=0).mean(), 2)
    return pd.DataFrame([rep])

def run():
    dcs_raw, stores_raw, transport_raw = load_raw()
    dcs, stores, transport = clean_tables(dcs_raw, stores_raw, transport_raw)
    dcs.to_csv(CLEAN_DIR/"dcs_clean.csv", index=False)
    stores.to_csv(CLEAN_DIR/"stores_clean.csv", index=False)
    transport.to_csv(CLEAN_DIR/"transport_clean.csv", index=False)
    dq = data_quality_report(dcs, stores, transport)
    dq.to_csv(CLEAN_DIR/"data_quality_report.csv", index=False)

if __name__ == "__main__":
    run()
