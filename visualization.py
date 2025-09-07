# visualization.py
# Produces PNG charts you can drag into PPT. Keep it simple and readable.

import pandas as pd
import matplotlib.pyplot as plt

from config import RESULTS_DIR, CLEAN_DIR, CHARTS_DIR, FIG_DPI

def _bar(x, y, title, xlabel, ylabel, fname):
    plt.figure()
    plt.bar(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / fname, dpi=FIG_DPI)
    plt.close()

def run():
    util = pd.read_csv(RESULTS_DIR / "dc_utilization.csv")
    cost_by_dc = pd.read_csv(RESULTS_DIR / "cost_by_dc.csv")
    cost_by_region = pd.read_csv(RESULTS_DIR / "cost_by_region.csv")
    stores = pd.read_csv(CLEAN_DIR / "stores_clean.csv")

    _bar(util["dc_id"], util["utilization_pct"], "DC Utilization (%)", "DC", "Utilization %", "dc_utilization.png")
    _bar(cost_by_dc["dc_id"], cost_by_dc["flow_cost_usd"], "Total Transport Cost by DC", "DC", "Cost (USD)", "cost_per_dc.png")
    plt.figure()
    plt.hist(stores["weekly_demand"], bins=20)
    plt.title("Distribution of Store Weekly Demand")
    plt.xlabel("Units")
    plt.ylabel("Count of Stores")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "demand_hist.png", dpi=FIG_DPI)
    plt.close()

if __name__ == "__main__":
    run()
