# app/frontend/app.py
import os, json, time, requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sqlite3
from st_aggrid import AgGrid, GridOptionsBuilder


BACKEND = "http://localhost:8000"
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = os.path.join("data", "warehouse.db")
DATA_DIR = BASE_DIR / "data"
CLEAN_DIR = DATA_DIR / "clean"
RESULTS_DIR = DATA_DIR / "results"
CHARTS_DIR = DATA_DIR / "charts"
ASSETS_DIR = BASE_DIR / "assets"

HD_ORANGE = "#F96302"
HD_DARK = "#0f1116"
HD_CARD_BG = "#161a23"

st.set_page_config(
    page_title="Supply Chain Digital Twin — Network Refresh",
    page_icon=str(ASSETS_DIR / "hd_favicon.png") if (ASSETS_DIR / "hd_favicon.png").exists() else "🧭",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {HD_DARK}; }}
      .metric-card {{
         background:{HD_CARD_BG}; border:1px solid rgba(255,255,255,0.08);
         border-radius:16px; padding:16px 18px; box-shadow:0 2px 10px rgba(0,0,0,0.25);
      }}
      .metric-title {{ color:rgba(255,255,255,0.7); font-size:.85rem; font-weight:600; }}
      .metric-value {{ color:#fff; font-size:1.8rem; font-weight:700; margin-top:6px; }}
      .hd-title {{ font-size:2.2rem; font-weight:800; color:#fff; margin:0 0 6px 0; }}
      .hd-sub {{ color:rgba(255,255,255,0.7); font-size:.95rem; margin-bottom:18px; }}
      .hd-accent {{ color:{HD_ORANGE}; }}
      .badge {{ display:inline-block; padding:4px 8px; border:1px solid rgba(255,255,255,0.1); border-radius:12px; color:#ddd; margin-right:8px; background:#141821; }}
      .delta-good {{ color:#16c784; font-weight:700; }}
      .delta-bad {{ color:#ff4d4f; font-weight:700; }}
      .stButton>button {{ background-color:{HD_ORANGE} !important; color:white !important; border-radius:10px; }}
    </style>
    """, unsafe_allow_html=True
)

# ------- utils -------
def fmt_money(x):
    try: return f"${float(x):,.0f}"
    except: return str(x)

def fmt_pct(x, p=1):
    try: return f"{float(x):.{p}f}%"
    except: return str(x)

def safe_get(url, method="get", json_payload=None):
    try:
        r = requests.post(url, json=json_payload, timeout=90) if method=="post" else requests.get(url, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def load_results():
    dfs={}
    def read_csv(path):
        try: return pd.read_csv(path)
        except: return pd.DataFrame()
    dfs["util"]=read_csv(RESULTS_DIR/"dc_utilization.csv")
    dfs["cost_by_dc"]=read_csv(RESULTS_DIR/"cost_by_dc.csv")
    dfs["cost_by_region"]=read_csv(RESULTS_DIR/"cost_by_region.csv")
    dfs["flows"]=read_csv(RESULTS_DIR/"optimal_flows.csv")
    dfs["stores"]=read_csv(CLEAN_DIR/"stores_clean.csv")
    dfs["dcs"]=read_csv(CLEAN_DIR/"dcs_clean.csv")
    dfs["transport"]=read_csv(CLEAN_DIR/"transport_clean.csv")
    return dfs

def kpi_json(): return safe_get(f"{BACKEND}/kpi") or {}
def run_full_pipeline():
    with st.spinner("Running full pipeline…"):
        res = safe_get(f"{BACKEND}/run/full","post")
        time.sleep(0.2)
        st.session_state["baseline_kpi"] = res
        st.session_state["last_scenario"] = {}
    return res
def run_scenario(dc_mult: dict, region_mult: dict):
    payload={"dc_capacity_mult": dc_mult, "region_demand_mult": region_mult}
    with st.spinner("Running scenario…"):
        res = safe_get(f"{BACKEND}/scenario/run","post",payload)
        time.sleep(0.2)
        st.session_state["last_scenario"] = payload
    return res

# ------- header -------
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:16px;">
      <div style="width:14px;height:28px;background:{HD_ORANGE};border-radius:3px;"></div>
      <div>
        <div class="hd-title">Supply Chain Digital Twin <span class="hd-accent">— Network Refresh</span></div>
        <div class="hd-sub">Executive dashboard, scenario planning, SQL-backed NLQ.</div>
      </div>
    </div>
    """, unsafe_allow_html=True
)

left, mid, right = st.columns([1.2,1,6])
with left:
    if st.button("Run Full Pipeline"): st.session_state["kpi"] = run_full_pipeline()
with mid: st.write("")

k = st.session_state.get("kpi") or kpi_json()
baseline = st.session_state.get("baseline_kpi", k)

# ------- KPI tiles (Exec row) -------
k1,k2,k3,k4 = st.columns(4)
for col, title, val in [
    (k1, "Total Cost (penalty incl.)", fmt_money(k.get("total_cost_with_penalty_usd",0))),
    (k2, "Transport Cost", fmt_money(k.get("total_transport_cost_usd",0))),
    (k3, "% Slow Lanes (>2 days)", fmt_pct(k.get("pct_units_on_slow_lanes",0))),
    (k4, "Unmet Units", f"{float(k.get('unmet_units',0)):,.0f}"),
]:
    with col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{val}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# ===================== DASHBOARD PAGE =====================
tab_dash, tab_map, tab_charts, tab_nlq, tab_sql = st.tabs(
    ["Dashboard", "Network Map", "Charts", "Ask the Network", "SQL Explorer"]
)

# -------- Dashboard tab (tiles from SQL endpoints) --------
with tab_dash:
    st.subheader("Dashboard")
    a,b = st.columns(2)

    # Top DC utilization
    with a:
        st.markdown("**Top DC Utilization**")
        data = safe_get(f"{BACKEND}/dashboard/util/top?n=10")
        if not data or "error" in data:
            st.warning("No utilization data yet. Run pipeline first.")
        elif isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data:
            if len(data) > 0:
                fig = go.Figure(go.Bar(
                    x=[d["dc_id"] for d in data],
                    y=[d["utilization_pct"] for d in data]
                ))
                fig.update_layout(
                    yaxis_title="Utilization %", xaxis_title="DC",
                    paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
                    font_color="white", margin=dict(l=40,r=20,t=10,b=40)
                )
                st.plotly_chart(fig, use_container_width=True)

    # Cost by DC
    with b:
        st.markdown("**Transport Cost by DC (Top 10)**")
        data = safe_get(f"{BACKEND}/dashboard/cost/by_dc?n=10&order=desc")
        if not data or "error" in data:
            st.warning("No DC cost data yet. Run pipeline first.")
        elif isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data:
            if len(data) > 0:
                fig = go.Figure(go.Bar(
                    x=[d["dc_id"] for d in data],
                    y=[d["flow_cost_usd"] for d in data]
                ))
                fig.update_layout(
                    yaxis_title="Cost (USD)", xaxis_title="DC",
                    paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
                    font_color="white", margin=dict(l=40,r=20,t=10,b=40)
                )
                st.plotly_chart(fig, use_container_width=True)

    # Cost by Region
    c,d = st.columns(2)
    with c:
        st.markdown("**Transport Cost by Region**")
        data = safe_get(f"{BACKEND}/dashboard/cost/by_region?n=4&order=desc")
        if not data or "error" in data:
            st.warning("No regional cost data yet. Run pipeline first.")
        elif isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data:
            if len(data) > 0:
                fig = go.Figure(go.Bar(
                    x=[d["region"] for d in data],
                    y=[d["flow_cost_usd"] for d in data]
                ))
                fig.update_layout(
                    yaxis_title="Cost (USD)", xaxis_title="Region",
                    paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
                    font_color="white", margin=dict(l=40,r=20,t=10,b=40)
                )
                st.plotly_chart(fig, use_container_width=True)

    # Demand Distribution (SQL-driven instead of PNG)
    with d:
        st.markdown("**Demand Distribution (from SQL)**")
        data = safe_get(f"{BACKEND}/dashboard/demand/dist")

        records = []

        if not data:
            st.warning("No demand data yet. Run pipeline first.")
        elif isinstance(data, dict):
            if "records" in data:
                records = data["records"]
            elif "error" in data:
                st.warning("No demand data yet. Run pipeline first.")
        elif isinstance(data, list):
            records = data

        if records and len(records) > 0:
            df = pd.DataFrame(records)
            if "weekly_demand" in df.columns:
                import plotly.express as px
                fig = px.histogram(df, x="weekly_demand", nbins=20,
                                title="Distribution of Store Weekly Demand")
                fig.update_layout(
                    paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
                    font_color="white", margin=dict(l=40, r=20, t=40, b=40),
                    yaxis_title="Count of Stores", xaxis_title="Units"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Column 'weekly_demand' not found in data.")



    # Scenario controls inline
    st.markdown("---")
    st.subheader("Scenario Controls")
    dfs = load_results()
    dc_list = dfs["dcs"]["dc_id"].tolist() if not dfs["dcs"].empty else []
    region_list = sorted(dfs["stores"]["region"].dropna().unique().tolist()) if not dfs["stores"].empty else []
    c1,c2 = st.columns(2)
    with c1:
        sel_dc = st.multiselect("Select DC(s)", options=dc_list, default=dc_list[:2] if dc_list else [])
        cap_mult = st.slider("Capacity multiplier", 0.2, 1.5, 0.9, 0.05)
    with c2:
        sel_region = st.multiselect("Select region(s)", options=region_list, default=region_list[:1] if region_list else [])
        dem_mult = st.slider("Demand multiplier", 0.5, 1.5, 1.10, 0.05)
    dc_mult = {dc: cap_mult for dc in sel_dc}
    region_mult = {rg: dem_mult for rg in sel_region}
    if st.button("Run Scenario"):
        if "baseline_kpi" not in st.session_state: st.session_state["baseline_kpi"] = k
        st.session_state["kpi"] = run_scenario(dc_mult, region_mult)
        k = st.session_state["kpi"]
        st.success("Scenario executed.")

    # Delta ribbon
    baseline = st.session_state.get("baseline_kpi", k)
    if baseline:
        def delta(curr, base): 
            try: return float(curr) - float(base)
            except: return 0.0
        rows = [
            ("Total Cost", delta(k.get("total_cost_with_penalty_usd",0), baseline.get("total_cost_with_penalty_usd",0))),
            ("Transport Cost", delta(k.get("total_transport_cost_usd",0), baseline.get("total_transport_cost_usd",0))),
            ("% Slow Lanes", delta(k.get("pct_units_on_slow_lanes",0), baseline.get("pct_units_on_slow_lanes",0))),
            ("Unmet Units", delta(k.get("unmet_units",0), baseline.get("unmet_units",0))),
        ]
        st.markdown("---")
        d1,d2,d3,d4 = st.columns(4)
        for col,(name, dval) in zip([d1,d2,d3,d4], rows):
            good = dval < 0  # lower is better for all four
            sign = "↓" if dval < 0 else "↑"
            txt = f"<span class='{'delta-good' if good else 'delta-bad'}'>{sign} {fmt_money(abs(dval)) if name!='% Slow Lanes' else f'{abs(dval):.1f}%'}</span>"
            with col: st.markdown(f"**Δ {name}**<br/>{txt}", unsafe_allow_html=True)

# -------- Network Map --------
with tab_map:
    st.subheader("Network Flow Map (Top Lanes)")
    dfs = load_results()
    if dfs["flows"].empty or dfs["dcs"].empty or dfs["stores"].empty or dfs["transport"].empty:
        st.warning("Run the pipeline first to generate flows/stores/dcs/transport.")
    else:
        flows = dfs["flows"].copy()
        dcs = dfs["dcs"][["dc_id","lat","lon"]].rename(columns={"lat":"dc_lat","lon":"dc_lon"})
        stores = dfs["stores"][["store_id","lat","lon","region"]].rename(columns={"lat":"st_lat","lon":"st_lon"})
        flows = flows.merge(dfs["transport"][["dc_id","store_id","service_time_days"]], on=["dc_id","store_id"], how="left")
        flows = flows.merge(dcs, on="dc_id", how="left").merge(stores, on="store_id", how="left")

        color_by_service = st.toggle("Color lanes by service time (>2 days in red)", value=True)
        top_n = st.slider("Show top N lanes by units", 50, 500, 200, 50)
        flows_top = flows.sort_values("units_assigned", ascending=False).head(top_n)

        fig = go.Figure()
        # DC markers
        fig.add_trace(go.Scattergeo(
            lon=dcs["dc_lon"], lat=dcs["dc_lat"], mode="markers",
            marker=dict(size=10, color="#ffffff", line=dict(color=HD_ORANGE, width=2)),
            name="DCs", hoverinfo="text", text=dcs["dc_id"], showlegend=True
        ))
        # Store markers
        stores_sample = stores.sample(min(250, len(stores)), random_state=42)
        fig.add_trace(go.Scattergeo(
            lon=stores_sample["st_lon"], lat=stores_sample["st_lat"],
            mode="markers", marker=dict(size=4, color="lightblue"),
            name="Stores", hoverinfo="text", text=stores_sample["store_id"], showlegend=True
        ))
        # Lines
        max_units = max(flows_top["units_assigned"].max(), 1.0)
        for r in flows_top.itertuples(index=False):
            color = HD_ORANGE
            if color_by_service and pd.notna(r.service_time_days) and r.service_time_days > 2.0:
                color = "#ff4d4f"
            fig.add_trace(go.Scattergeo(
                lon=[r.dc_lon, r.st_lon], lat=[r.dc_lat, r.st_lat],
                mode="lines",
                line=dict(width=max(1, r.units_assigned/max_units*6), color=color),
                opacity=0.55, hoverinfo="text",
                text=f"{r.dc_id} → {r.store_id}<br>Units: {int(r.units_assigned):,}<br>SLA: {r.service_time_days:.1f}d",
                showlegend=False
            ))
        fig.update_layout(
            geo=dict(scope="north america", projection_type="albers usa",
                     showcountries=True, countrycolor="rgba(255,255,255,0.2)",
                     showland=True, landcolor="#1b2130", lakecolor="#1b2130",
                     subunitcolor="rgba(255,255,255,0.1)", coastlinecolor="rgba(255,255,255,0.2)",
                     bgcolor=HD_DARK),
            paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig, use_container_width=True)

# -------- Charts (existing PNGs) --------
with tab_charts:
    st.subheader("Charts")
    colA, colB = st.columns(2)
    def show_png(name, title, col):
        path = CHARTS_DIR / name
        if path.exists(): 
            with col: st.markdown(f"**{title}**"); st.image(str(path), use_container_width=True)
        else:
            with col: st.warning(f"{name} not found. Run the pipeline.")
    show_png("dc_utilization.png", "DC Utilization (%)", colA)
    show_png("cost_per_dc.png", "Transport Cost by DC (USD)", colB)
    show_png("cost_by_region.png", "Transport Cost by Region (USD)", colA)
    show_png("demand_hist.png", "Store Weekly Demand Distribution", colB)

# -------- Ask the Network (deterministic SQL) --------
with tab_nlq:
    st.subheader("Ask the network (SQL-backed, deterministic)")
    q = st.text_input("Question", "Which DC has the highest utilization?")
    if st.button("Ask"):
        try:
            r = requests.post(f"{BACKEND}/nlq", json={"question": q}, timeout=30)
            r.raise_for_status()
            data = r.json()
            st.success(data.get("answer","(no answer)"))
            src = data.get("source","")
            st.caption(f"_source: {src}_")
            st.text_area("Copy answer", data.get("answer",""), height=120)
        except Exception as e:
            st.error(f"(NLQ error) {e}")

st.caption("Connect Tableau to data/results/*.csv for an exec deck. SQL warehouse: data/warehouse.db")

# -------- SQL Explorer --------
with tab_sql:
    st.subheader("SQL Explorer")
    st.markdown("Run ad-hoc queries directly against the SQLite warehouse (`data/warehouse.db`).")

    default_query = "SELECT * FROM dc_utilization LIMIT 10;"
    sql_query = st.text_area("Enter SQL query", default_query, height=120)

    if st.button("Run Query"):
        try:
            con = sqlite3.connect(DB_PATH)
            df = pd.read_sql(sql_query, con)
            con.close()

            if not df.empty:
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_default_column(filter=True, sortable=True, resizable=True)
                gridOptions = gb.build()

                AgGrid(df, gridOptions=gridOptions, theme="streamlit", height=400, fit_columns_on_grid_load=True)

                # Download button
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "query_results.csv", "text/csv")
            else:
                st.info("Query returned no results.")
        except Exception as e:
            st.error(f"Error running query: {e}")
