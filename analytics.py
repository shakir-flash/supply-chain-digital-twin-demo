# analytics.py
# Helper aggregations for PPT/tableau

import pandas as pd
from config import CLEAN_DIR, RESULTS_DIR

def run():
    flows = pd.read_csv(RESULTS_DIR / "optimal_flows.csv")
    dcs = pd.read_csv(CLEAN_DIR / "dcs_clean.csv")
    stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")

    # Cost by DC
    cost_by_dc = flows.groupby("dc_id")["flow_cost_usd"].sum().reset_index().sort_values("flow_cost_usd", ascending=False)
    cost_by_dc.to_csv(RESULTS_DIR / "cost_by_dc.csv", index=False)

    # Stores served by each DC
    served = flows.groupby("dc_id")["store_id"].nunique().reset_index().rename(columns={"store_id": "stores_served"})
    served.to_csv(RESULTS_DIR / "stores_served_by_dc.csv", index=False)

    # Region view (based on store region)
    flows_region = flows.merge(stores[["store_id", "region"]], on="store_id", how="left")
    cost_by_region = flows_region.groupby("region")["flow_cost_usd"].sum().reset_index().sort_values("flow_cost_usd", ascending=False)
    cost_by_region.to_csv(RESULTS_DIR / "cost_by_region.csv", index=False)

if __name__ == "__main__":
    run()
