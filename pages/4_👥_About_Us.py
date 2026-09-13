"""Meet the team behind SmartStock AI."""

import streamlit as st


TEAM = [
    (
        "Kashif",
        "Lead AI Architect & Data Scientist",
        "TL",
        "Shapes SmartStock AI's data strategy, forecasting architecture, and responsible AI roadmap.",
        "https://www.linkedin.com/in/muhammad-kashif-ansari-842b22159/",
        "https://github.com/Kashif-ansari",
    ),
    (
        "Ahsan",
        "Machine Learning Engineer",
        "ML",
        "Builds and evaluates time-series models that turn sales history into dependable demand signals.",
        "https://www.linkedin.com/in/muhammad-ahsan-59120522",
        "https://github.com/ahsan14262",
    ),
    (
        "Zeeshan",
        "RAG & Knowledge Systems Developer",
        "RK",
        "Connects product knowledge, FAISS retrieval, and Groq reasoning into practical inventory advice.",
        "https://www.linkedin.com/in/zeeshan-ansari-555583424",
        "https://github.com/M-Zeeshan834",
    ),
    (
        "Aamir",
        "Full-Stack Streamlit UI/UX Designer",
        "UX",
        "Designs clear, fast workflows that help commerce teams move from insight to action.",
        "https://www.linkedin.com/in/amir-iqbal-7a3b7231b",
        "https://github.com/Kashif-ansari",
    ),
    (
        "Qasim",
        "Data Engineering & Ingestion Specialist",
        "DE",
        "Makes multi-format sales and stock data clean, reliable, and ready for analysis.",
        "https://www.linkedin.com/in/muhammad-kashif-ansari-842b22159/",
        "https://github.com/Kashif-ansari",
    ),
    (
        "Muhammad",
        "Business Intelligence & Domain Analyst",
        "BI",
        "Translates retail operations needs into useful KPIs, replenishment rules, and decision support.",
        "https://www.linkedin.com/in/muhammad-kashif-ansari-842b22159/",
        "https://github.com/Kashif-ansari",
    ),
]

st.markdown(
    """
    <style>
        .team-hero {
            padding: 2.7rem 2.3rem; border-radius: 22px; color: white;
            background: linear-gradient(115deg, #0F172A, #1E88E5 65%, #00C853);
            box-shadow: 0 18px 36px rgba(30, 136, 229, .18); margin-bottom: 1.8rem;
        }
        .team-hero h1 { color: white !important; margin: 0; }
        .team-hero p { color: #e0f2fe; font-size: 1.08rem; margin: .65rem 0 0; max-width: 780px; }
        .team-card {
            min-height: 290px; padding: 1.4rem; border-radius: 18px;
            border: 1px solid #dbeafe; background: rgba(255,255,255,.92);
            box-shadow: 0 8px 20px rgba(15,23,42,.07); margin-bottom: 1.2rem;
        }
        .avatar-placeholder {
            display: inline-flex; width: 54px; height: 54px; align-items: center; justify-content: center;
            border-radius: 50%; color: white; font-weight: 800; letter-spacing: .05em;
            background: linear-gradient(135deg, #00C853, #1E88E5);
        }
        .block-container {
            max-width: 1400px;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .team-card h3 { color: #0f172a !important; margin: .8rem 0 .2rem; }
        .role { color: #1E88E5; font-weight: 700; min-height: 2.8rem; }
        .contribution { color: #475569; min-height: 4.8rem; line-height: 1.5; }
        .social-links a { color: #0077b5; font-weight: 700; text-decoration: none; margin-right: .9rem; }
    </style>
    <section class="team-hero">
        <h1>Meet the team behind SmartStock AI</h1>
        <p>We are building a calmer, smarter way for commerce teams to balance availability, working capital, and customer delight—one confident inventory decision at a time.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

#st.caption("Replace the member labels, avatars, and placeholder social profiles with your team’s details when ready.")

for start in range(0, len(TEAM), 3):
    columns = st.columns(3, gap="large")
    for column, (name, role, initials, contribution, linkedin_url, github_url) in zip(columns, TEAM[start : start + 3]):
        with column:
            with st.container():
                st.markdown(
                    f"""
                    <article class="team-card">
                        <div class="avatar-placeholder" aria-label="Avatar placeholder for {name}">{initials}</div>
                        <h3>{name}</h3>
                        <div class="role">{role}</div>
                        <p class="contribution">{contribution}</p>
                        <div class="social-links">
                            {f'<a href="{linkedin_url}" target="_blank">LinkedIn ↗</a>' if linkedin_url else ''}
                            {f'<a href="{github_url}" target="_blank">GitHub ↗</a>' if github_url else ''}
                        </div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
