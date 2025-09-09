import streamlit as st
from typing import List

def render_suggested_questions(
    suggestions: List[str],
    target_key: str = "nlq_query",
    title: str = "Try asking",
    columns: int = 3,
    auto_run_flag: str = "nlq_autorun",
):
    """
    Renders a compact suggestions bar with clickable pills.
    Clicking a pill writes the question into st.session_state[target_key]
    and sets st.session_state[auto_run_flag] = True so the caller can run the query.

    Parameters
    ----------
    suggestions : list of strings to show as preset questions
    target_key  : the st.session_state key for your NLQ text_input
    title       : small heading above the suggestions
    columns     : how many columns to lay the pills out
    auto_run_flag : session key set to True when a suggestion is clicked
    """
    if not suggestions:
        return

    st.markdown(
        """
        <style>
            .sg-wrap { 
                padding: .5rem .75rem; 
                border-radius: 12px; 
                background: rgba(0,0,0,0.03); 
                border: 1px solid rgba(0,0,0,0.06);
                margin-top: .25rem;
            }
            .sg-title {
                font-size: 0.90rem; 
                font-weight: 700; 
                opacity: .90; 
                margin-bottom: .25rem;
            }
            .sg-pill > button {
                width: 100%;
                border-radius: 999px !important;
                font-size: 0.90rem !important;
                padding: .35rem .75rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="sg-wrap"><div class="sg-title">💡 {title}:</div>', unsafe_allow_html=True)

    # Lay out pills in a grid
    cols = st.columns(columns)
    for i, q in enumerate(suggestions):
        with cols[i % columns]:
            if st.button(q, key=f"sg_{target_key}_{i}", use_container_width=True):
                st.session_state[target_key] = q
                st.session_state[auto_run_flag] = True

    st.markdown("</div>", unsafe_allow_html=True)
