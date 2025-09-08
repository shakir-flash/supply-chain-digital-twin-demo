# model/optimization.py
import numpy as np, pandas as pd
from scipy.optimize import linprog
from config import CLEAN_DIR, RESULTS_DIR, UNMET_PENALTY

def run():
    stores = pd.read_csv(CLEAN_DIR/"stores_clean.csv")
    dcs = pd.read_csv(CLEAN_DIR/"dcs_clean.csv")
    transport = pd.read_csv(CLEAN_DIR/"transport_clean.csv")

    store_ids = stores["store_id"].tolist()
    dc_ids = dcs["dc_id"].tolist()
    demand = stores.set_index("store_id")["weekly_demand"].to_dict()
    capacity = dcs.set_index("dc_id")["weekly_capacity"].to_dict()

    pairs = list(zip(transport["dc_id"], transport["store_id"]))
    n_ship = len(pairs)

    c_ship = transport["cost_per_unit_usd"].to_numpy()
    c_unmet = np.full(len(store_ids), UNMET_PENALTY)
    c = np.concatenate([c_ship, c_unmet], axis=0)

    A_eq = np.zeros((len(store_ids), n_ship + len(store_ids)))
    b_eq = np.zeros(len(store_ids))
    s_idx = {s:i for i,s in enumerate(store_ids)}
    for j,(dc,st) in enumerate(pairs):
        A_eq[s_idx[st], j] = 1.0
    for i,s in enumerate(store_ids):
        A_eq[i, n_ship+i] = 1.0
        b_eq[i] = demand[s]

    A_ub = np.zeros((len(dc_ids), n_ship + len(store_ids)))
    b_ub = np.zeros(len(dc_ids))
    d_idx = {d:i for i,d in enumerate(dc_ids)}
    for j,(dc,st) in enumerate(pairs):
        A_ub[d_idx[dc], j] = 1.0
    for d,i in d_idx.items():
        b_ub[i] = capacity[d]

    bounds = [(0, None)] * (n_ship + len(store_ids))

    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"LP solve failed: {res.message}")

    x = res.x[:n_ship]
    u = res.x[n_ship:]

    flows = []
    for idx,(dc,st) in enumerate(pairs):
        qty = x[idx]
        if qty > 1e-6:
            cost_unit = float(transport.iloc[idx]["cost_per_unit_usd"])
            flows.append({"dc_id":dc, "store_id":st, "units_assigned":qty, "cost_per_unit_usd":cost_unit})
    flows_df = pd.DataFrame(flows)
    flows_df["flow_cost_usd"] = flows_df["units_assigned"] * flows_df["cost_per_unit_usd"]
    flows_df.to_csv(RESULTS_DIR/"optimal_flows.csv", index=False)

    unmet_df = pd.DataFrame({"store_id":store_ids, "unmet_units":u})
    unmet_df.to_csv(RESULTS_DIR/"unmet_demand.csv", index=False)

    util = flows_df.groupby("dc_id")["units_assigned"].sum().reset_index()
    util_df = dcs[["dc_id","weekly_capacity"]].merge(util, on="dc_id", how="left")
    util_df["units_assigned"] = util_df["units_assigned"].fillna(0)
    util_df["utilization_pct"] = (util_df["units_assigned"]/util_df["weekly_capacity"]*100).round(2)
    util_df.to_csv(RESULTS_DIR/"dc_utilization.csv", index=False)

    penalty_cost = float((unmet_df["unmet_units"] * UNMET_PENALTY).sum())
    total_cost = float(flows_df["flow_cost_usd"].sum()) + penalty_cost
    kpi = pd.DataFrame([
        {"metric":"total_transport_cost_usd","value":round(float(flows_df["flow_cost_usd"].sum()),2)},
        {"metric":"unmet_penalty_usd","value":round(penalty_cost,2)},
        {"metric":"total_cost_with_penalty_usd","value":round(total_cost,2)},
        {"metric":"total_units","value":float(sum(demand.values()))},
        {"metric":"num_dcs","value":len(dc_ids)},
        {"metric":"num_stores","value":len(store_ids)},
        {"metric":"lp_status","value":"optimal"},
    ])
    kpi.to_csv(RESULTS_DIR/"kpi_summary.csv", index=False)

if __name__ == "__main__":
    run()
