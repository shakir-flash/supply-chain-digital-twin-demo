# analytics.py
# KPI aggregations, including service-level (slow lanes)

import pandas as pd
from config import CLEAN_DIR, RESULTS_DIR

def run():
    flows = pd.read_csv(RESULTS_DIR / "optimal_flows.csv")
    dcs = pd.read_csv(CLEAN_DIR / "dcs_clean.csv")
    stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")
    transport = pd.read_csv(CLEAN_DIR / "transport_clean.csv")

    # Cost by DC
    cost_by_dc = flows.groupby("dc_id")["flow_cost_usd"].sum().reset_index().sort_values("flow_cost_usd", ascending=False)
    cost_by_dc.to_csv(RESULTS_DIR / "cost_by_dc.csv", index=False)

    # Stores served
    served = flows.groupby("dc_id")["store_id"].nunique().reset_index().rename(columns={"store_id": "stores_served"})
    served.to_csv(RESULTS_DIR / "stores_served_by_dc.csv", index=False)

    # Cost by region
    flows_region = flows.merge(stores[["store_id", "region"]], on="store_id", how="left")
    cost_by_region = flows_region.groupby("region")["flow_cost_usd"].sum().reset_index().sort_values("flow_cost_usd", ascending=False)
    cost_by_region.to_csv(RESULTS_DIR / "cost_by_region.csv", index=False)

    # SLA: slow lanes > 2 days
    flows_serv = flows.merge(transport[["dc_id","store_id","service_time_days"]], on=["dc_id","store_id"], how="left")
    slow = flows_serv.loc[flows_serv["service_time_days"] > 2.0]
    slow_kpis = pd.DataFrame([{
        "slow_lanes_count": int(slow.shape[0]),
        "units_on_slow_lanes": float(slow["units_assigned"].sum()),
        "pct_units_on_slow_lanes": float(100.0 * slow["units_assigned"].sum() / max(flows["units_assigned"].sum(), 1.0))
    }])
    slow.to_csv(RESULTS_DIR / "slow_lanes_detail.csv", index=False)
    slow_kpis.to_csv(RESULTS_DIR / "slow_lanes_kpis.csv", index=False)

if __name__ == "__main__":
    run()
