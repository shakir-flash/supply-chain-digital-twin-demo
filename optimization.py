# optimization.py
# Min-cost DC->Store assignment using linear programming (SciPy linprog).
# If you prefer PuLP/OR-Tools, swap in your solver easily.

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from config import CLEAN_DIR, RESULTS_DIR

def run():
    # Load cleaned inputs
    stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")
    dcs = pd.read_csv(CLEAN_DIR / "dcs_clean.csv")
    transport = pd.read_csv(CLEAN_DIR / "transport_clean.csv")

    store_ids = stores["store_id"].tolist()
    dc_ids = dcs["dc_id"].tolist()
    demand = stores.set_index("store_id")["weekly_demand"].to_dict()
    capacity = dcs.set_index("dc_id")["weekly_capacity"].to_dict()

    # Variable order: all (dc, store) pairs present in transport
    pairs = list(zip(transport["dc_id"], transport["store_id"]))
    n_vars = len(pairs)

    c = transport["cost_per_unit_usd"].to_numpy()

    # Equality constraints: for each store, sum_i x[i,j] = demand[j]
    A_eq = np.zeros((len(store_ids), n_vars))
    b_eq = np.zeros(len(store_ids))
    store_index = {s: k for k, s in enumerate(store_ids)}

    for var_idx, (dc, st) in enumerate(pairs):
        if st in store_index:
            A_eq[store_index[st], var_idx] = 1.0
    for s, k in store_index.items():
        b_eq[k] = demand[s]

    # Inequality constraints: for each DC, sum_j x[i,j] <= capacity[i]
    A_ub = np.zeros((len(dc_ids), n_vars))
    b_ub = np.zeros(len(dc_ids))
    dc_index = {i: k for k, i in enumerate(dc_ids)}

    for var_idx, (dc, st) in enumerate(pairs):
        if dc in dc_index:
            A_ub[dc_index[dc], var_idx] = 1.0
    for i, k in dc_index.items():
        b_ub[k] = capacity[i]

    bounds = [(0, None)] * n_vars

    # Solve
    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub,
                  A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")

    if not res.success:
        raise RuntimeError(f"LP solve failed: {res.message}")

    # Build flows
    x = res.x
    flows = []
    for idx, (dc, st) in enumerate(pairs):
        qty = x[idx]
        if qty > 1e-6:
            cost_unit = float(transport.loc[idx, "cost_per_unit_usd"])
            flows.append({
                "dc_id": dc,
                "store_id": st,
                "units_assigned": qty,
                "cost_per_unit_usd": cost_unit
            })
    flows_df = pd.DataFrame(flows)
    flows_df["flow_cost_usd"] = flows_df["units_assigned"] * flows_df["cost_per_unit_usd"]
    flows_df.to_csv(RESULTS_DIR / "optimal_flows.csv", index=False)

    # ---- FIXED: DC utilization (merge-based to avoid length mismatch)
    util = flows_df.groupby("dc_id")["units_assigned"].sum().reset_index()
    util_df = dcs[["dc_id", "weekly_capacity"]].merge(util, on="dc_id", how="left")
    util_df["units_assigned"] = util_df["units_assigned"].fillna(0)
    util_df["utilization_pct"] = (
        util_df["units_assigned"] / util_df["weekly_capacity"] * 100
    ).round(2)
    util_df.to_csv(RESULTS_DIR / "dc_utilization.csv", index=False)

    # KPIs
    kpi = pd.DataFrame([
        {"metric": "total_transport_cost_usd",
         "value": round(float(flows_df["flow_cost_usd"].sum()), 2)},
        {"metric": "total_units", "value": float(sum(demand.values()))},
        {"metric": "num_dcs", "value": len(dc_ids)},
        {"metric": "num_stores", "value": len(store_ids)},
        {"metric": "lp_status", "value": "optimal"},
    ])
    kpi.to_csv(RESULTS_DIR / "kpi_summary.csv", index=False)

if __name__ == "__main__":
    run()
