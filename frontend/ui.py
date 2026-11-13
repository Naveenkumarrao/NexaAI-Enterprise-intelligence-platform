import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --nexa-ink: #172b4d;
            --nexa-muted: #63748b;
            --nexa-primary: #315efb;
            --nexa-border: #e5eaf2;
            --nexa-surface: #ffffff;
            --primary-color: #315efb;
        }
        [data-testid="stAppViewContainer"] {
            background: #f5f7fb;
            color: var(--nexa-ink);
        }
        [data-testid="stHeader"] { background: transparent; }
        .main .block-container {
            max-width: 1280px;
            padding: 2rem 2.5rem 3rem;
        }
        h1, h2, h3 { color: var(--nexa-ink); letter-spacing: -0.025em; }
        h1 { font-size: 2rem !important; font-weight: 700 !important; }
        [data-testid="stCaptionContainer"] {
            color: var(--nexa-muted);
            font-size: 0.95rem;
        }
        [data-testid="stMetric"] {
            background: var(--nexa-surface);
            border: 1px solid var(--nexa-border);
            border-radius: 12px;
            padding: 1rem 1.15rem;
        }
        [data-testid="stMetricLabel"] { color: var(--nexa-muted); }
        [data-testid="stMetricValue"] { color: var(--nexa-ink); font-weight: 700; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--nexa-surface);
            border-color: var(--nexa-border);
            border-radius: 12px;
        }
        [data-testid="stExpander"] {
            background: var(--nexa-surface);
            border: 1px solid var(--nexa-border);
            border-radius: 10px;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--nexa-border);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--nexa-muted);
        }
        .nexa-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0 1.2rem;
            margin-bottom: 0.8rem;
            border-bottom: 1px solid var(--nexa-border);
        }
        .nexa-brand-mark {
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            color: #fff;
            background: linear-gradient(135deg, #315efb, #7448e8);
            font-size: 1.15rem;
            font-weight: 800;
        }
        .nexa-brand-name { color: var(--nexa-ink); font-weight: 750; }
        .nexa-brand-caption {
            color: var(--nexa-muted);
            font-size: 0.75rem;
            margin-top: 0.15rem;
        }
        .page-eyebrow {
            color: var(--nexa-primary);
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
        }
        .page-divider {
            border-bottom: 1px solid var(--nexa-border);
            margin: 1rem 0 1.5rem;
        }
        div.stButton > button[kind="primary"] {
            background: var(--nexa-primary);
            border-color: var(--nexa-primary);
            border-radius: 8px;
            font-weight: 650;
            min-height: 2.65rem;
        }
        div.stButton > button {
            border-radius: 8px;
            font-weight: 550;
        }
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            border-radius: 8px;
        }
        [data-testid="stAlert"] { border-radius: 10px; }
        button[role="tab"] { font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
        <div class="nexa-brand">
            <div class="nexa-brand-mark">N</div>
            <div>
                <div class="nexa-brand-name">Nexa AI</div>
                <div class="nexa-brand-caption">Enterprise intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, section: str = "AI WORKSPACE") -> None:
    st.markdown(f'<div class="page-eyebrow">{section}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)
    st.markdown('<div class="page-divider"></div>', unsafe_allow_html=True)
