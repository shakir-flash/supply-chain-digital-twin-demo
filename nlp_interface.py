# nlp_interface.py
# Lightweight, rule-based NLQ over results. Script a few demo Q&A for your interview.

import pandas as pd
from config import RESULTS_DIR

def load():
    util = pd.read_csv(RESULTS_DIR / "dc_utilization.csv")
    kpi = pd.read_csv(RESULTS_DIR / "kpi_summary.csv")
    flows = pd.read_csv(RESULTS_DIR / "optimal_flows.csv")
    return util, kpi, flows

def ask(q: str) -> str:
    ql = q.lower().strip()
    util, kpi, flows = load()

    if "highest utilization" in ql:
        r = util.loc[util["utilization_pct"].idxmax()]
        return f"{r['dc_id']} has the highest utilization at {r['utilization_pct']:.1f}%."
    if "lowest utilization" in ql:
        r = util.loc[util["utilization_pct"].idxmin()]
        return f"{r['dc_id']} has the lowest utilization at {r['utilization_pct']:.1f}%."
    if "total transport cost" in ql or ("total" in ql and "cost" in ql):
        v = kpi.loc[kpi["metric"]=="total_transport_cost_usd","value"].astype(float).iloc[0]
        return f"Total optimized transport cost is ${float(v):,.0f}."
    if "stores served by" in ql:
        # e.g., "stores served by DC01?"
        tokens = q.replace("?", "").split()
        dc = next((t for t in tokens if t.upper().startswith(("DC", "DFC", "FDC", "PRO", "FL_"))), None)
        if not dc:
            return "Please specify a DC id."
        dc = dc.strip().upper()
        subset = flows.loc[flows["dc_id"] == dc]
        if subset.empty:
            return f"No flows found for {dc}."
        stores = subset["store_id"].tolist()
        return f"{dc} serves {len(stores)} stores: {', '.join(stores[:10])}{'...' if len(stores)>10 else ''}"
    if "most expensive lanes" in ql or ("top" in ql and "expensive" in ql):
        top = flows.sort_values("cost_per_unit_usd", ascending=False).head(5)
        pairs = [f"{r.dc_id}->{r.store_id} (${r.cost_per_unit_usd:.2f})" for r in top.itertuples(index=False)]
        return "Top expensive lanes (by unit cost): " + ", ".join(pairs)

    return "Try: 'Which DC has the highest utilization?', 'Total transport cost?', or 'Stores served by DFC_Dallas_TX?'"

if __name__ == "__main__":
    for q in [
        "Which DC has the highest utilization?",
        "Which DC has the lowest utilization?",
        "What is the total transport cost?",
        "Stores served by DFC_Dallas_TX?",
        "Top most expensive lanes"
    ]:
        print("Q:", q)
        print("A:", ask(q))
        print()
