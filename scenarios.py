# scenarios.py
# Apply scenario tweaks (capacity cuts, demand surges), rerun pipeline.

import pandas as pd
import json

from config import CLEAN_DIR
from optimization import run as run_opt
from analytics import run as run_an
from visualization import run as run_viz

def apply_scenario(cfg: dict):
    dcs = pd.read_csv(CLEAN_DIR / "dcs_clean.csv")
    stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")

    # Apply DC capacity multipliers
    for dc_id, mult in cfg.get("dc_capacity_mult", {}).items():
        dcs.loc[dcs["dc_id"] == dc_id, "weekly_capacity"] *= float(mult)

    # Apply regional demand multipliers
    for region, mult in cfg.get("region_demand_mult", {}).items():
        stores.loc[stores["region"] == region, "weekly_demand"] *= float(mult)

    dcs.to_csv(CLEAN_DIR / "dcs_clean.csv", index=False)
    stores.to_csv(CLEAN_DIR / "stores_clean.csv", index=False)

if __name__ == "__main__":
    # Example:
    # python scenarios.py '{"dc_capacity_mult":{"FDC_DALLAS_TX":0.9},"region_demand_mult":{"Southeast":1.1}}'
    import sys
    cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    apply_scenario(cfg)
    run_opt()
    run_an()
    run_viz()
    print("Scenario applied and solved. See results in data/results and data/charts.")
