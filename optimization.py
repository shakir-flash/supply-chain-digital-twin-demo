# optimization.py
# Min-cost DC->Store assignment using linear programming (SciPy linprog).
# Now supports unmet demand with penalty cost.

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

    # Variables: x[i,j] = shipped units, u[j] = unmet demand
    pairs = list(zip(transport["dc_id"], transport["store_id"]))
    n_ship = len(pairs)

    UNMET_PENALTY = 10.0  # $ penalty per unit unmet demand

    c_ship = transport["cost_per_unit_usd"].to_numpy()
    c_unmet = np.full(len(store_ids), UNMET_PENALTY)
    c = np.concatenate([c_ship, c_unmet], axis=0)

    # Equality: meet each store's demand (ship + unmet = demand)
    A_eq = np.zeros((len(store_ids), n_ship + len(store_ids)))
    b_eq = np.zeros(len(store_ids))
    store_index = {s: k for k, s in enumerate(store_ids)}

    for col_idx, (dc, st) in enumerate(pairs):
        if st in store_index:
            A_eq[store_index[st], col_idx] = 1.0
    for j_idx, s in enumerate(store_ids):
        A_eq[j_idx, n_ship + j_idx] = 1.0
        b_eq[j_idx] = demand[s]

    # Inequality: DC capacity
    A_ub = np.zeros((len(dc_ids), n_ship + len(store_ids)))
    b_ub = np.zeros(len(dc_ids))
    dc_index = {i: k for k, i in enumerate(dc_ids)}

    for col_idx, (dc, st) in enumerate(pairs):
        if dc in dc_index:
            A_ub[dc_index[dc], col_idx] = 1.0
    for i, k in dc_index.items():
        b_ub[k] = capacity[i]

    bounds = [(0, None)] * (n_ship + len(store_ids))

    # Solve LP
    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub,
                  A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"LP solve failed: {res.message}")

    # Parse results
    x = res.x[:n_ship]
    u = res.x[n_ship:]

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

    unmet_df = pd.DataFrame({"store_id": store_ids, "unmet_units": u})
    unmet_df.to_csv(RESULTS_DIR / "unmet_demand.csv", index=False)

    # Utilization
    util = flows_df.groupby("dc_id")["units_assigned"].sum().reset_index()
    util_df = dcs[["dc_id", "weekly_capacity"]].merge(util, on="dc_id", how="left")
    util_df["units_assigned"] = util_df["units_assigned"].fillna(0)
    util_df["utilization_pct"] = (util_df["units_assigned"] / util_df["weekly_capacity"] * 100).round(2)
    util_df.to_csv(RESULTS_DIR / "dc_utilization.csv", index=False)

    # KPIs
    penalty_cost = float((unmet_df["unmet_units"] * UNMET_PENALTY).sum())
    total_cost = float(flows_df["flow_cost_usd"].sum()) + penalty_cost

    kpi = pd.DataFrame([
        {"metric": "total_transport_cost_usd", "value": round(float(flows_df["flow_cost_usd"].sum()), 2)},
        {"metric": "unmet_penalty_usd", "value": round(penalty_cost, 2)},
        {"metric": "total_cost_with_penalty_usd", "value": round(total_cost, 2)},
        {"metric": "total_units", "value": float(sum(demand.values()))},
        {"metric": "num_dcs", "value": len(dc_ids)},
        {"metric": "num_stores", "value": len(store_ids)},
        {"metric": "lp_status", "value": "optimal"},
    ])
    kpi.to_csv(RESULTS_DIR / "kpi_summary.csv", index=False)

if __name__ == "__main__":
    run()
