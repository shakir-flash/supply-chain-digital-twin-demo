import os, time, requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder
from components.hd_header import render_header
from components.suggested_questions import render_suggested_questions

render_header(
    logo_path="assets/hd_favicon.png",  # update if your path is different
    company="The Home Depot",
    interview_title="Supply Chain Digital Twin, Interview Demo",
    candidate_name="Shakir Ahmed",
    subtitle="Scenario planning, cost tradeoffs, and service risk",
    location="United States",
    contact="datashakir0585@email.com",
    tags=["Lean KPIs", "Total cost", "Transport cost", "Unmet units"],
    show_divider=True,
    sticky=False,          # set True if you want the header to stay on top while scrolling
    hide_streamlit_chrome=True
)

# ---------- Config ----------
BACKEND = "http://localhost:8000"
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CLEAN_DIR = DATA_DIR / "clean"
RESULTS_DIR = DATA_DIR / "results"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = os.path.join("data", "warehouse.db")

HD_ORANGE = "#F96302"
HD_DARK = "#0f1116"
HD_CARD_BG = "#161a23"

st.set_page_config(
    page_title="Supply Chain Digital Twin, Network Refresh",
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
      .delta-good {{ color:#16c784; font-weight:700; }}
      .delta-bad {{ color:#ff4d4f; font-weight:700; }}
      .summary-pill {{
        background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08);
        padding:10px 12px; border-radius:12px; color:#fff; font-size:0.95rem; margin-right:8px;
      }}
    </style>
    """, unsafe_allow_html=True
)

# ---------- helpers ----------
def fmt_money(x):
    try:
        return f"${float(x):,.0f}"
    except:
        return str(x)

def fmt_pct(x, p=1):
    try:
        return f"{float(x):.{p}f}%"
    except:
        return str(x)

def safe_get(url, method="get", json_payload=None):
    try:
        if method == "post":
            r = requests.post(url, json=json_payload, timeout=90)
        else:
            r = requests.get(url, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def load_results():
    dfs = {}
    def read_csv(path):
        try:
            return pd.read_csv(path)
        except:
            return pd.DataFrame()
    dfs["util"] = read_csv(RESULTS_DIR / "dc_utilization.csv")
    dfs["cost_by_dc"] = read_csv(RESULTS_DIR / "cost_by_dc.csv")
    dfs["cost_by_region"] = read_csv(RESULTS_DIR / "cost_by_region.csv")
    dfs["flows"] = read_csv(RESULTS_DIR / "optimal_flows.csv")
    dfs["stores"] = read_csv(CLEAN_DIR / "stores_clean.csv")
    dfs["dcs"] = read_csv(CLEAN_DIR / "dcs_clean.csv")
    return dfs

# ---------- header ----------
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:16px;">
      <div style="width:14px;height:28px;background:{HD_ORANGE};border-radius:3px;"></div>
      <div>
        <div class="hd-title">Supply Chain Digital Twin, <span class="hd-accent"> Network Refresh</span></div>
        <div class="hd-sub">Executive dashboard, scenario planning, SQL-backed insights.</div>
      </div>
    </div>
    """, unsafe_allow_html=True
)

# ---------- controls row ----------
left, mid, right = st.columns([1.2, 1, 6])
with left:
    if st.button("Run Full Pipeline"):
        with st.spinner("Running full pipeline…"):
            res = safe_get(f"{BACKEND}/run/full", "post")
            st.session_state["kpi"] = res
            st.session_state["baseline_kpi"] = res
            st.session_state["last_scenario"] = {}
            st.success("Pipeline completed.")
with mid:
    st.write("")

# ---------- KPI tiles (3 only: Total cost, Transport cost, Unmet units) ----------
k = st.session_state.get("kpi") or safe_get(f"{BACKEND}/kpi")
k1, k2, k3 = st.columns(3)
tiles = [
    ("Total Cost (penalty incl.)", fmt_money(k.get("total_cost_with_penalty_usd", 0))),
    ("Transport Cost", fmt_money(k.get("total_transport_cost_usd", 0))),
    ("Unmet Units", f"{float(k.get('unmet_units', 0)):,.0f}"),
]
for col, (title, val) in zip([k1, k2, k3], tiles):
    with col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{val}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# ---------- Executive Summary bar ----------
ins = safe_get(f"{BACKEND}/insights/summary")
if isinstance(ins, dict) and "error" not in ins:
    pills = []
    pills.append(f"Total cost: <b>{fmt_money(ins.get('total_cost_with_penalty_usd', 0))}</b>")
    pills.append(f"Avg DC utilization: <b>{fmt_pct(ins.get('avg_utilization_pct', 0))}</b>")
    pills.append(f"DCs >80%: <b>{int(ins.get('num_dcs_over_80', 0))}</b> | >90%: <b>{int(ins.get('num_dcs_over_90', 0))}</b>")
    tr = ins.get("top_cost_region") or "—"
    share = ins.get("top_cost_region_share_pct", 0.0)
    pills.append(f"Top cost region: <b>{tr}</b> ({share:.1f}% of regional cost)")
    st.markdown(
        "<div>" + " ".join([f"<span class='summary-pill'>{p}</span>" for p in pills]) + "</div>",
        unsafe_allow_html=True,
    )
else:
    st.info("Run the pipeline to populate the summary.")

# ===================== TABS =====================
tab_dash, tab_map, tab_nlq, tab_sql = st.tabs(
    ["Dashboard", "Network Map", "Ask the Network", "SQL Explorer"]
)

# -------- Dashboard --------
with tab_dash:
    st.subheader("Dashboard")

    a, b = st.columns(2)

    # Top DC Utilization
    with a:
        st.markdown("**Top DC Utilization**")
        data = safe_get(f"{BACKEND}/dashboard/util/top?n=10")
        if isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data and isinstance(data, list) and len(data) > 0:
            fig = go.Figure(go.Bar(x=[d["dc_id"] for d in data], y=[d["utilization_pct"] for d in data]))
            fig.update_layout(
                yaxis_title="Utilization %",
                xaxis_title="DC",
                paper_bgcolor=HD_DARK,
                plot_bgcolor=HD_DARK,
                font_color="white",
                margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Run the pipeline to populate utilization.")

    # Transport Cost by DC (Top 10)
    with b:
        st.markdown("**Transport Cost by DC (Top 10)**")
        data = safe_get(f"{BACKEND}/dashboard/cost/by_dc?n=10&order=desc")
        if isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data and isinstance(data, list) and len(data) > 0:
            fig = go.Figure(go.Bar(x=[d["dc_id"] for d in data], y=[d["flow_cost_usd"] for d in data]))
            fig.update_layout(
                yaxis_title="Cost (USD)",
                xaxis_title="DC",
                paper_bgcolor=HD_DARK,
                plot_bgcolor=HD_DARK,
                font_color="white",
                margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No DC cost data.")

    c, d = st.columns(2)
    # Transport Cost by Region
    with c:
        st.markdown("**Transport Cost by Region**")
        data = safe_get(f"{BACKEND}/dashboard/cost/by_region?n=4&order=desc")
        if isinstance(data, dict) and "records" in data:
            data = data["records"]
        if data and isinstance(data, list) and len(data) > 0:
            fig = go.Figure(go.Bar(x=[d["region"] for d in data], y=[d["flow_cost_usd"] for d in data]))
            fig.update_layout(
                yaxis_title="Cost (USD)",
                xaxis_title="Region",
                paper_bgcolor=HD_DARK,
                plot_bgcolor=HD_DARK,
                font_color="white",
                margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No regional cost data.")

    # Demand Distribution (from SQL)
    with d:
        st.markdown("**Demand Distribution (from SQL)**")
        data = safe_get(f"{BACKEND}/dashboard/demand/dist")
        records = []
        if isinstance(data, dict) and "records" in data:
            records = data["records"]
        elif isinstance(data, list):
            records = data
        if records:
            df = pd.DataFrame(records)
            if "weekly_demand" in df.columns:
                fig = px.histogram(
                    df, x="weekly_demand", nbins=20, title="Distribution of Store Weekly Demand"
                )
                fig.update_layout(
                    paper_bgcolor=HD_DARK,
                    plot_bgcolor=HD_DARK,
                    font_color="white",
                    margin=dict(l=40, r=20, t=40, b=40),
                    yaxis_title="Count of Stores",
                    xaxis_title="Units",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Column 'weekly_demand' not found in data.")
        else:
            st.warning("No demand data yet. Run pipeline first.")

    # ---------- Scenario controls + deltas ----------
    st.markdown("---")
    st.subheader("Scenario Controls")
    dfs = load_results()
    dc_list = dfs["dcs"]["dc_id"].tolist() if not dfs["dcs"].empty else []
    region_list = sorted(dfs["stores"]["region"].dropna().unique().tolist()) if not dfs["stores"].empty else []
    c1, c2 = st.columns(2)
    with c1:
        sel_dc = st.multiselect("Select DC(s)", options=dc_list, default=dc_list[:2] if dc_list else [])
        cap_mult = st.slider("Capacity multiplier", 0.2, 1.5, 0.9, 0.05)
    with c2:
        sel_region = st.multiselect("Select region(s)", options=region_list, default=region_list[:1] if region_list else [])
        dem_mult = st.slider("Demand multiplier", 0.5, 1.5, 1.10, 0.05)
    dc_mult = {dc: cap_mult for dc in sel_dc}
    region_mult = {rg: dem_mult for rg in sel_region}
    if st.button("Run Scenario"):
        payload = {"dc_capacity_mult": dc_mult, "region_demand_mult": region_mult}
        with st.spinner("Running scenario…"):
            res = safe_get(f"{BACKEND}/scenario/run", "post", payload)
            st.session_state["kpi"] = res
            if "baseline_kpi" not in st.session_state:
                st.session_state["baseline_kpi"] = res
            st.session_state["last_scenario"] = payload
            st.success("Scenario executed.")

    # Delta ribbon
    baseline = st.session_state.get("baseline_kpi", k)
    current = st.session_state.get("kpi", k)
    if baseline and current:
        def delta(curr, base):
            try:
                return float(curr) - float(base)
            except:
                return 0.0
        rows = [
            ("Total Cost", delta(current.get("total_cost_with_penalty_usd", 0), baseline.get("total_cost_with_penalty_usd", 0))),
            ("Transport Cost", delta(current.get("total_transport_cost_usd", 0), baseline.get("total_transport_cost_usd", 0))),
            ("Unmet Units", delta(current.get("unmet_units", 0), baseline.get("unmet_units", 0))),
        ]
        st.markdown("---")
        d1, d2, d3 = st.columns(3)
        for col, (name, dval) in zip([d1, d2, d3], rows):
            good = dval < 0
            sign = "↓" if dval < 0 else "↑"
            fmt_val = fmt_money(abs(dval)) if name != "Unmet Units" else f"{abs(dval):,.0f}"
            txt = f"<span class='{'delta-good' if good else 'delta-bad'}'>{sign} {fmt_val}</span>"
            with col:
                st.markdown(f"**Δ {name}**<br/>{txt}", unsafe_allow_html=True)

# -------- Network Map --------
with tab_map:
    st.subheader("Network Flow Map (Top Lanes)")
    dfs = load_results()

    # Load transport_clean directly (not in dfs)
    try:
        transport_df = pd.read_csv(CLEAN_DIR / "transport_clean.csv")
    except Exception:
        transport_df = pd.DataFrame()

    if dfs["flows"].empty or dfs["dcs"].empty or dfs["stores"].empty or transport_df.empty:
        st.warning("Run the pipeline first to generate flows / stores / DCs / transport.")
    else:
        flows = dfs["flows"].copy()
        dcs = dfs["dcs"][["dc_id", "lat", "lon"]].rename(columns={"lat": "dc_lat", "lon": "dc_lon"})
        stores = dfs["stores"][["store_id", "lat", "lon", "region"]].rename(columns={"lat": "st_lat", "lon": "st_lon"})

        # join service time + coordinates
        flows = flows.merge(
            transport_df[["dc_id", "store_id", "service_time_days"]],
            on=["dc_id", "store_id"], how="left"
        ).merge(dcs, on="dc_id", how="left").merge(stores, on="store_id", how="left")

        color_by_service = st.toggle("Color lanes by service time (> 2 days in red)", value=True)
        top_n = st.slider("Show top N lanes by units", 50, 500, 200, 50)
        flows_top = flows.sort_values("units_assigned", ascending=False).head(top_n)

        fig = go.Figure()

        # DC markers (white dot with HD orange ring)
        fig.add_trace(go.Scattergeo(
            lon=dcs["dc_lon"], lat=dcs["dc_lat"], mode="markers",
            marker=dict(size=10, color="#ffffff", line=dict(color=HD_ORANGE, width=2)),
            name="DCs", hoverinfo="text", text=dcs["dc_id"], showlegend=True
        ))

        # Store markers (sample to avoid clutter)
        stores_sample = stores.sample(min(250, len(stores)), random_state=42) if len(stores) else stores
        if not stores_sample.empty:
            fig.add_trace(go.Scattergeo(
                lon=stores_sample["st_lon"], lat=stores_sample["st_lat"],
                mode="markers", marker=dict(size=4, color="lightblue"),
                name="Stores", hoverinfo="text", text=stores_sample["store_id"], showlegend=True
            ))

        # Lines (width ∝ units; red if service_time_days > 2)
        max_units = max(float(flows_top["units_assigned"].max() or 0), 1.0)
        for r in flows_top.itertuples(index=False):
            color = HD_ORANGE
            sla_days = r.service_time_days if pd.notna(r.service_time_days) else None
            if color_by_service and (sla_days is not None) and (sla_days > 2.0):
                color = "#ff4d4f"
            lw = max(1.0, (float(r.units_assigned) / max_units) * 6.0)
            sla_str = f"{sla_days:.1f}d" if sla_days is not None else "n/a"

            fig.add_trace(go.Scattergeo(
                lon=[r.dc_lon, r.st_lon], lat=[r.dc_lat, r.st_lat],
                mode="lines",
                line=dict(width=lw, color=color),
                opacity=0.55, hoverinfo="text",
                text=f"{r.dc_id} → {r.store_id}<br>Units: {int(r.units_assigned):,}<br>SLA: {sla_str}",
                showlegend=False
            ))

        fig.update_layout(
            geo=dict(
                scope="usa",                       # valid with "albers usa"
                projection_type="albers usa",
                showcountries=True, countrycolor="rgba(255,255,255,0.2)",
                showland=True, landcolor="#1b2130", lakecolor="#1b2130",
                subunitcolor="rgba(255,255,255,0.1)", coastlinecolor="rgba(255,255,255,0.2)",
                bgcolor=HD_DARK
            ),
            paper_bgcolor=HD_DARK, plot_bgcolor=HD_DARK,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig, use_container_width=True)




# -------- Ask the Network --------
with tab_nlq:
    st.subheader("Ask the Network")

    # Suggested questions (simple static box)
    st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 14px;
        color: #f5f5f5;
        font-size: 0.95rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);">
        <span style="font-weight:600; font-size:1rem; color:#FFA559;"> Suggested questions you can ask:</span>
        <ul style="margin-top:8px; line-height:1.6;">
            <li>What is the total cost?</li>
            <li>What is the transport cost?</li>
            <li>How many unmet units?</li>
            <li>Show unmet units by region</li>
            <li>Top DCs by utilization</li>
            <li>Bottom DCs by utilization</li>
            <li>Which lanes are the slowest?</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

    # Input box
    q = st.text_input("Question", "Which DC has the highest utilization?")

    if st.button("Ask"):
        resp = safe_get(f"{BACKEND}/nlq", "post", {"question": q})
        if isinstance(resp, dict) and "answer" in resp:
            st.success(resp["answer"])
        else:
            st.warning("I couldn't generate an answer for that.")


# -------- SQL Explorer --------
with tab_sql:
    st.subheader("SQL Explorer")
    st.markdown(
        f"Run ad-hoc queries against the SQLite warehouse (<code>{DB_PATH}</code>). No <code>;</code> needed.",
        unsafe_allow_html=True,
    )

    templates = {
        "Top DC utilization": "SELECT dc_id, utilization_pct FROM dc_utilization ORDER BY utilization_pct DESC LIMIT 10",
        "Transport cost by DC": "SELECT dc_id, flow_cost_usd FROM cost_by_dc ORDER BY flow_cost_usd DESC LIMIT 10",
        "Transport cost by Region": "SELECT region, flow_cost_usd FROM cost_by_region ORDER BY flow_cost_usd DESC",
        "Stores with unmet demand": "SELECT * FROM unmet_demand WHERE unmet_units > 0 ORDER BY unmet_units DESC LIMIT 20",
        "Flows sample": "SELECT * FROM optimal_flows LIMIT 50",
    }
    c1, c2 = st.columns([1, 3])
    with c1:
        chosen = st.selectbox("Templates", list(templates.keys()), index=0)
    with c2:
        default_query = templates[chosen]
        sql_query = st.text_area("Enter SQL query (read-only)", default_query, height=120)

    if st.button("Run Query"):
        try:
            payload = {"query": sql_query, "max_rows": 5000}
            resp = requests.post(f"{BACKEND}/sql/run", json=payload, timeout=60)
            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                df = pd.DataFrame(data.get("records", []))
                if df.empty:
                    st.info("Query returned no results.")
                else:
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_default_column(filter=True, sortable=True, resizable=True)
                    gridOptions = gb.build()
                    AgGrid(df, gridOptions=gridOptions, theme="streamlit", height=420, fit_columns_on_grid_load=True)

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("Download CSV", csv, "query_results.csv", "text/csv")
        except Exception as e:
            st.error(f"Error running query: {e}")

