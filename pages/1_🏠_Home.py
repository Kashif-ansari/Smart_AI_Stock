"""Modern e-commerce home dashboard for SmartStock AI."""

import streamlit as st


st.markdown(
    """
    <style>
        .home-hero {
            padding: 3.2rem 2.5rem;
            border-radius: 24px;
            color: #ffffff;
            background: radial-gradient(circle at 85% 15%, rgba(255,255,255,.22), transparent 28%),
                        linear-gradient(125deg, #006E2E, #00C853 45%, #1E88E5);
            box-shadow: 0 20px 44px rgba(0, 125, 77, .22);
            margin-bottom: 1.8rem;
        }
        .home-hero h1 { color: #ffffff !important; font-size: clamp(2.3rem, 5vw, 4rem); margin: 0; }
        .home-hero p { color: #ecfdf5; font-size: 1.15rem; margin: .65rem 0 0; }
        .eyebrow { letter-spacing: .12em; font-size: .76rem; font-weight: 800; text-transform: uppercase; opacity: .9; }
        .solution-card, .feature-card {
            height: 100%; padding: 1.35rem; border-radius: 16px;
            background: rgba(255,255,255,.88); border: 1px solid #e2e8f0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, .06);
        }
        .solution-card h3, .feature-card h3 { margin: .35rem 0 .5rem; color: #0f172a !important; }
        .solution-card p, .feature-card p { color: #475569; margin: 0; }
        .feature-icon { font-size: 1.9rem; }
        .section-kicker { color: #1E88E5; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }
    </style>
    <section class="home-hero">
        <div class="eyebrow">Retail intelligence, simplified</div>
        <h1>SmartStock AI</h1>
        <p>AI-Powered Demand Forecasting &amp; Smart Inventory Optimization</p>
    </section>
    """,
    unsafe_allow_html=True,
)

metrics = st.columns(3)
metrics[0].metric("Forecast confidence", "94.2%", "+2.4%")
metrics[1].metric("Stock health", "Healthy", "+8.1%")
metrics[2].metric("Products monitored", "1,248", "+126 this month")

st.markdown("<p class='section-kicker'>Solve the costly trade-off</p>", unsafe_allow_html=True)
problem, solution = st.columns(2, gap="large")
with problem:
    st.markdown(
        """
        <div class="solution-card">
            <div class="feature-icon">⚖️</div><h3>Overstocking vs. stockouts</h3>
            <p>See demand before it happens, so capital does not sit on slow sellers and customers do not meet empty shelves.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with solution:
    st.markdown(
        """
        <div class="solution-card">
            <div class="feature-icon">🗓️</div><h3>Dual-calendar alignment</h3>
            <p>Plan around both Gregorian trading cycles and Hijri events such as Ramadan and Eid.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

scenario = st.select_slider(
    "Explore the inventory balance",
    options=["Overstock risk", "Balanced", "Stockout risk"],
    value="Balanced",
    help="A lightweight preview of the decision support SmartStock AI provides.",
)
scenario_copy = {
    "Overstock risk": ("Working capital alert", "Reduce replenishment on slow-moving products and protect margin."),
    "Balanced": ("Inventory is in balance", "Keep monitoring forecast changes and seasonal demand signals."),
    "Stockout risk": ("Replenishment alert", "Prioritize items whose predicted demand exceeds stock on hand."),
}
headline, detail = scenario_copy[scenario]
st.info(f"**{headline}:** {detail}")

st.markdown("<p class='section-kicker'>Built for the complete inventory workflow</p>", unsafe_allow_html=True)
features = [
    ("🔮", "Pretrained Time-Series Forecasting", "Turn daily sales history into next-week demand signals."),
    ("🌙", "Gregorian & Islamic Calendar Awareness", "Make seasonal plans that account for Ramadan and Eid."),
    ("📁", "Multi-Format Data Ingestion", "Bring CSV, Excel, JSON, or SQLite exports into one workflow."),
    ("💬", "RAG-Powered Inventory Advisor", "Ask grounded inventory questions with Groq + FAISS."),
]
for row_start in range(0, len(features), 2):
    columns = st.columns(2, gap="large")
    for column, (icon, title, description) in zip(columns, features[row_start : row_start + 2]):
        with column:
            st.markdown(
                f"<div class='feature-card'><div class='feature-icon'>{icon}</div><h3>{title}</h3><p>{description}</p></div>",
                unsafe_allow_html=True,
            )

st.divider()
st.subheader("Ready to make your next replenishment decision?")
forecast_action, advisor_action, _ = st.columns([1, 1, 2])
with forecast_action:
    if st.button("Create a forecast  →", type="primary", use_container_width=True):
        st.switch_page("pages/2_📊_Demand_Forecasting.py")
with advisor_action:
    if st.button("Ask inventory advisor  →", use_container_width=True):
        st.switch_page("pages/3_📦_Smart_Inventory_RAG.py")
