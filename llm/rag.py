# llm/rag.py
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import SEMANTIC_DIR, RESULTS_DIR
import pandas as pd

IDX_PATH = SEMANTIC_DIR / "tfidf.pkl"
CORPUS_PATH = SEMANTIC_DIR / "corpus.txt"

_vectorizer = None
_docs = []

def build_corpus():
    # Build small corpus from KPI CSVs and data dictionary stub
    texts = []
    def add(name, text):
        texts.append(f"### {name}\n{text}")

    # KPI summary
    try:
        kpi = pd.read_csv(RESULTS_DIR/"kpi_summary.csv").to_string(index=False)
        add("kpi_summary.csv", kpi)
    except: pass

    # Slow lanes
    try:
        slow = pd.read_csv(RESULTS_DIR/"slow_lanes_kpis.csv").to_string(index=False)
        add("slow_lanes_kpis.csv", slow)
    except: pass

    # Data dictionary (tiny)
    dd = """
    Fields:
    - dc_utilization.csv: dc_id, weekly_capacity, units_assigned, utilization_pct
    - cost_by_region.csv: region, flow_cost_usd
    - optimal_flows.csv: dc_id, store_id, units_assigned, cost_per_unit_usd, flow_cost_usd
    - unmet_demand.csv: store_id, unmet_units
    KPIs: total_transport_cost_usd, unmet_penalty_usd, total_cost_with_penalty_usd, pct_units_on_slow_lanes, unmet_units
    """
    add("data_dictionary", dd)

    CORPUS_PATH.write_text("\n\n".join(texts), encoding="utf-8")
    return texts

def load_index():
    global _vectorizer, _docs
    if not CORPUS_PATH.exists():
        _docs = build_corpus()
    else:
        _docs = CORPUS_PATH.read_text(encoding="utf-8").split("\n\n")
    _vectorizer = TfidfVectorizer(stop_words="english")
    _X = _vectorizer.fit_transform(_docs)
    return _vectorizer, _X, _docs

def retrieve_context(query: str, k=3) -> str:
    vec, X, docs = load_index()
    q = vec.transform([query])
    sims = cosine_similarity(q, X).flatten()
    top = sims.argsort()[::-1][:k]
    return "\n\n".join(docs[i] for i in top)
