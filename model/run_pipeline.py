# model/run_pipeline.py
from etl.data_generation import run as gen_run
from etl.data_cleaning import run as clean_run
from model.optimization import run as opt_run
from analytics.kpi import build as kpi_build
from analytics.viz import run as viz_run

def run_full():
    gen_run()
    clean_run()
    opt_run()
    kpi_build()
    viz_run()

def run_scenario(levers: dict):
    """
    levers example:
    {
      "dc_capacity_mult": {"FDC_Dallas_TX": 0.9},
      "region_demand_mult": {"Southeast": 1.1}
    }
    """
    import pandas as pd
    from config import CLEAN_DIR
    dcs = pd.read_csv(CLEAN_DIR/"dcs_clean.csv")
    stores = pd.read_csv(CLEAN_DIR/"stores_clean.csv")

    for dc_id, mult in levers.get("dc_capacity_mult", {}).items():
        dcs.loc[dcs["dc_id"]==dc_id, "weekly_capacity"] *= float(mult)

    for region, mult in levers.get("region_demand_mult", {}).items():
        stores.loc[stores["region"]==region, "weekly_demand"] *= float(mult)

    dcs.to_csv(CLEAN_DIR/"dcs_clean.csv", index=False)
    stores.to_csv(CLEAN_DIR/"stores_clean.csv", index=False)

    opt_run()
    kpi_build()
    viz_run()
