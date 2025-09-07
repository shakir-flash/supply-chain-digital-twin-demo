# data_generation.py
# Generates messy, realistic synthetic datasets for DCs, stores, and transport lanes.

import random
import numpy as np
import pandas as pd

from config import (
    RAW_DIR, FACILITY_SEEDS, STORE_METROS, N_STORES, MAX_STORE_PER_METRO,
    STORE_WEEKLY_MEAN, STORE_WEEKLY_STD, DC_WEEKLY_CAP_MEAN, DC_WEEKLY_CAP_STD,
    MIN_STORE_DEMAND, MIN_DC_CAPACITY, BASE_RATE_PER_MILE, HANDLING_USD
)
from utils.geo import haversine_distance_miles, service_days

def _jitter(val, low=-0.25, high=0.25):
    return val + random.uniform(low, high)

def generate_dcs():
    rows = []
    for seed in FACILITY_SEEDS:
        cap = int(np.random.normal(DC_WEEKLY_CAP_MEAN, DC_WEEKLY_CAP_STD))
        rows.append({
            "dc_id": seed["dc_id"],
            "type": seed["type"],
            "city": seed["city"],
            "state": seed["state"],
            "lat": round(seed["lat"] + random.uniform(-0.05, 0.05), 4),
            "lon": round(seed["lon"] + random.uniform(-0.05, 0.05), 4),
            "weekly_capacity": max(cap, MIN_DC_CAPACITY),
            "fixed_cost_usd_wk": int(np.random.normal(250_000, 50_000))
        })
    dcs = pd.DataFrame(rows)
    # introduce messiness
    dcs = pd.concat([dcs, dcs.sample(1, random_state=1)], ignore_index=True)   # duplicate one row
    for idx in np.random.choice(dcs.index, size=min(2, len(dcs)), replace=False):
        dcs.loc[idx, "weekly_capacity"] = np.nan
    return dcs

def generate_stores():
    # distribute stores across metros
    stores = []
    remaining = N_STORES
    for metro in STORE_METROS:
        k = min(remaining, random.randint(2, MAX_STORE_PER_METRO))
        remaining -= k
        for i in range(k):
            demand = int(np.random.normal(STORE_WEEKLY_MEAN, STORE_WEEKLY_STD))
            stores.append({
                "store_id": f"STR_{metro['metro'].split(',')[0].replace(' ', '')[:6].upper()}_{i+1:02d}",
                "metro": metro["metro"],
                "region": metro["region"],
                "lat": round(_jitter(metro["lat"]), 4),
                "lon": round(_jitter(metro["lon"]), 4),
                "weekly_demand": max(demand, MIN_STORE_DEMAND)
            })
        if remaining <= 0:
            break
    stores_df = pd.DataFrame(stores)

    # messiness: duplicate a few, null region or demand randomly
    if len(stores_df) > 0:
        dupn = max(1, len(stores_df)//40)
        stores_df = pd.concat([stores_df, stores_df.sample(dupn)], ignore_index=True)
        for idx in np.random.choice(stores_df.index, size=min(6, len(stores_df)), replace=False):
            if random.random() < 0.5:
                stores_df.loc[idx, "weekly_demand"] = np.nan
            else:
                stores_df.loc[idx, "region"] = None
    return stores_df

def generate_transport(dcs_df: pd.DataFrame, stores_df: pd.DataFrame):
    rows = []
    for _, dc in dcs_df.iterrows():
        for _, st in stores_df.iterrows():
            dist = haversine_distance_miles(dc["lat"], dc["lon"], st["lat"], st["lon"])
            cost = BASE_RATE_PER_MILE * dist + HANDLING_USD + np.random.normal(0, 0.25)
            rows.append({
                "dc_id": dc["dc_id"], "store_id": st["store_id"],
                "distance_mi": round(dist, 2),
                "cost_per_unit_usd": round(max(cost, 0.10), 2),
                "service_time_days": round(service_days(dist), 2)
            })
    return pd.DataFrame(rows)

def run():
    dcs_raw = generate_dcs()
    stores_raw = generate_stores()
    transport_raw = generate_transport(dcs_raw.drop_duplicates("dc_id"), stores_raw.drop_duplicates("store_id"))

    dcs_raw.to_csv(RAW_DIR / "dcs_raw.csv", index=False)
    stores_raw.to_csv(RAW_DIR / "stores_raw.csv", index=False)
    transport_raw.to_csv(RAW_DIR / "transport_raw.csv", index=False)

if __name__ == "__main__":
    run()
