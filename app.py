"""SmartStock AI — Streamlit application entry point."""

import streamlit as st


st.set_page_config(
    page_title="SmartStock AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    """Apply the shared SmartStock AI visual system."""
    st.markdown(
        """
        <style>
            :root {
                --smartstock-green: #00C853;
                --smartstock-blue: #1E88E5;
                --smartstock-ink: #0F172A;
                --smartstock-surface: #FFFFFF;
                --smartstock-muted: #64748B;
            }

            .stApp {
                background: linear-gradient(135deg, #F8FAFC 0%, #EEF8F2 100%);
            }

            [data-testid="stSidebar"] {
                background: #0F172A;
            }

            [data-testid="stSidebar"] * { color: #E2E8F0; }
            [data-testid="stSidebarNav"] a:hover {
                background: rgba(0, 200, 83, 0.16);
                border-radius: 8px;
            }

            h1, h2, h3 { color: var(--smartstock-ink); font-weight: 700; }
            .smartstock-hero {
                padding: 2rem;
                border-radius: 18px;
                color: white;
                background: linear-gradient(115deg, #00C853, #1E88E5);
                box-shadow: 0 12px 30px rgba(30, 136, 229, 0.22);
            }
            .smartstock-hero h1, .smartstock-hero p { color: white; margin: 0; }
            .stButton > button {
                background: linear-gradient(90deg, #00C853, #1E88E5);
                color: white;
                border: 0;
                border-radius: 8px;
                font-weight: 600;
            }
            [data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 0.75rem;
            }
            @media (prefers-color-scheme: dark) {
                .stApp { background: #0B1120; }
                h1, h2, h3 { color: #F8FAFC; }
                [data-testid="stMetric"] { background: #172033; border-color: #334155; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_theme()

st.markdown(
    """
    <div class="smartstock-hero">
        <h1>SmartStock AI</h1>
        <p>Demand intelligence and inventory decisions for modern commerce.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("Use the sidebar to explore forecasting, inventory insights, and our team.")

