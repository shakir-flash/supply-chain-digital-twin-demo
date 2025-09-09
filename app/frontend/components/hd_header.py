import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import streamlit as st

# Color tokens
HD_ORANGE = "#F96302"
HD_ORANGE_2 = "#FF7A1A"
INK = "#0F172A"
PAPER = "#FFFFFF"

def _img_to_base64(p: str) -> Optional[str]:
    try:
        b = Path(p).read_bytes()
        return base64.b64encode(b).decode("utf-8")
    except Exception:
        return None

def render_header(
    logo_path: Optional[str] = None,
    company: str = "The Home Depot",
    interview_title: str = "Supply Chain Digital Twin, Interview Demo",
    candidate_name: str = "Shakir Ahmed",
    subtitle: Optional[str] = "Scenario planning, cost tradeoffs, and service risk",
    location: Optional[str] = "Virtual, America/Phoenix",
    contact: Optional[str] = None,
    date_str: Optional[str] = None,
    tags: Optional[List[str]] = None,
    show_divider: bool = True,
    sticky: bool = False,
    hide_streamlit_chrome: bool = True,
):
    """
    Render an elegant Home Depot header with your own logo.

    Drop-in usage: call render_header(...) at the very top of your Streamlit app, before any other layout.

    Arguments:
        logo_path: local path to your Home Depot logo, for example 'app/frontend/assets/thd_logo.png'
        company, interview_title, candidate_name, subtitle: text content
        location, contact, date_str: meta row, date default is today
        tags: small badges under the title
        show_divider: thin divider below the header
        sticky: keep the header fixed at the top of the viewport
        hide_streamlit_chrome: hides Streamlit default header and toolbar for a clean interview look
    """
    # Page config and chrome
    try:
        st.set_page_config(page_title="Supply Chain Digital Twin", page_icon="🧰", layout="wide")
    except Exception:
        # set_page_config can only be called once, ignore if already set
        pass

    if hide_streamlit_chrome:
        st.markdown(
            """
            <style>
                [data-testid="stToolbar"] { display: none !important; }
                header[data-testid="stHeader"] { display: none !important; }
                footer { visibility: hidden; }
                .block-container { padding-top: 1.0rem; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # Defaults
    if date_str is None:
        date_str = datetime.today().strftime("%b %d, %Y")
    if tags is None:
        tags = ["Lean KPIs", "Total cost", "Transport cost", "Unmet units"]

    # Build logo html
    logo_html = ""
    if logo_path:
        b64 = _img_to_base64(logo_path)
        if b64:
            logo_html = f"""
            <img alt="Home Depot Logo" src="data:image/png;base64,{b64}"
                 style="height:44px;width:auto;display:block;border-radius:8px;"/>
            """
        else:
            # graceful fallback mini mark in HD orange
            logo_html = f"""
            <svg width="44" height="44" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{company} logo">
              <rect width="36" height="36" rx="8" fill="{HD_ORANGE}"></rect>
              <path d="M8 24 L18 12 L28 24" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"></path>
              <rect x="12" y="24" width="12" height="2.5" rx="1.2" fill="white"></rect>
            </svg>
            """

    # Styles
    position_css = "position:sticky; top:0; z-index: 1000;" if sticky else ""
    st.markdown(
        f"""
        <style>
            .hd-wrap {{
                {position_css}
                background:
                    linear-gradient(135deg, #D94E02 0%, #F96302 40%, #B54400 100%);
                color: #FFFFFF;
                border-radius: 18px;
                padding: 18px 20px;
                box-shadow: 0 8px 20px rgba(185, 68, 0, 0.35);
                margin-bottom: 16px;
            }}
            .hd-row {{
                display: flex;
                align-items: center;
                gap: 16px;
                flex-wrap: wrap;
            }}
            .hd-logo {{
                display:flex;
                align-items:center;
                justify-content:center;
                height: 44px;
                width: 44px;
                border-radius: 10px;
                background: rgba(255,255,255,0.12);
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.18);
                overflow: hidden;
            }}
            .hd-titlebox {{
                display:flex;
                flex-direction: column;
                gap: 2px;
                min-width: 260px;
            }}
            .hd-kicker {{
                font-size: .8rem;
                letter-spacing: .02em;
                text-transform: uppercase;
                opacity: .92;
                font-weight: 800;
            }}
            .hd-title {{
                font-size: 1.25rem;
                font-weight: 800;
                line-height: 1.25;
                margin: 0;
            }}
            .hd-sub {{
                font-size: .95rem;
                opacity: .96;
                margin-top: 2px;
            }}
            .hd-meta {{
                display:flex;
                gap: 14px;
                flex-wrap: wrap;
                margin-top: 6px;
                font-size: .88rem;
                opacity: .95;
            }}
            .hd-badges {{
                display:flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-top: 10px;
            }}
            .hd-badge {{
                background: rgba(255,255,255,0.16);
                border: 1px solid rgba(255,255,255,0.28);
                color: {PAPER};
                padding: 4px 10px;
                border-radius: 999px;
                font-size: .82rem;
                font-weight: 700;
                backdrop-filter: blur(2px);
                white-space: nowrap;
            }}
            .hd-right {{
                margin-left: auto;
                text-align: right;
                display:flex;
                flex-direction: column;
                gap: 4px;
                align-items: flex-end;
            }}
            .hd-name {{
                font-weight: 800;
            }}
            .hd-pillbar {{
                display:flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-top: 8px;
                opacity: .95;
            }}
            .hd-pill {{
                font-size: .82rem;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 999px;
                background: rgba(255,255,255,0.10);
                border: 1px dashed rgba(255,255,255,0.35);
            }}
            .hd-divider {{
                height: 1px;
                width: 100%;
                background: linear-gradient(90deg, rgba(255,255,255,0.10), rgba(255,255,255,0.55), rgba(255,255,255,0.10));
                margin: 10px 0 2px 0;
                border-radius: 1px;
            }}
            @media (max-width: 900px) {{
                .hd-right {{ text-align: left; align-items: flex-start; margin-left: 0; }}
                .hd-title {{ font-size: 1.05rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Compose text bits
    kicker_html = f"<div class='hd-kicker'>{company}</div>"
    title_html = f"<div class='hd-title'>{interview_title}</div>"
    sub_html = f"<div class='hd-sub'>Presented by <span class='hd-name'>{candidate_name}</span></div>"

    meta_bits = []
    if location:
        meta_bits.append(f"• {location}")
    if contact:
        meta_bits.append(contact)
    if date_str:
        meta_bits.append(date_str)
    meta_html = " &nbsp;•&nbsp; ".join(meta_bits)

    badges_html = "".join(f"<span class='hd-badge'>{b}</span>" for b in tags)

    # Optional quick nav pills, non interactive, for a premium look without changing behavior
    pill_html = "".join(
        f"<span class='hd-pill'>{label}</span>"
        for label in ["Overview", "Costs", "Utilization", "Transport map", "Scenarios"]
    )

    # Render
    st.markdown(
        f"""
        <div class="hd-wrap">
            <div class="hd-row">
                <div class="hd-logo">{logo_html}</div>
                <div class="hd-titlebox">
                    {kicker_html}
                    {title_html}
                    {sub_html}
                    <div class="hd-meta">{meta_html}</div>
                    <div class="hd-badges">{badges_html}</div>
                </div>
                <div class="hd-right">
                    <div class="hd-pillbar">{pill_html}</div>
                </div>
            </div>
            {"<div class='hd-divider'></div>" if show_divider else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )