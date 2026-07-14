import streamlit as st


THEMES = {
    "Vert pastel": {"fond": "#f4faf6", "carte": "#ffffff", "primaire": "#4f8a68", "accent": "#dcefe3", "texte": "#19352a", "bordure": "#c7dfd0"},
    "Orange pastel": {"fond": "#fff8f1", "carte": "#ffffff", "primaire": "#bf7440", "accent": "#f9e4d3", "texte": "#4a2b18", "bordure": "#efd0b7"},
    "Bleu pastel": {"fond": "#f3f8fc", "carte": "#ffffff", "primaire": "#477da3", "accent": "#dcecf7", "texte": "#18364b", "bordure": "#c6deef"},
    "Gris pastel": {"fond": "#f6f7f8", "carte": "#ffffff", "primaire": "#68747e", "accent": "#e4e8eb", "texte": "#273038", "bordure": "#d1d7dc"},
    "Violet pastel": {"fond": "#faf6fc", "carte": "#ffffff", "primaire": "#85629b", "accent": "#eee1f4", "texte": "#3d284a", "bordure": "#ddcbe7"},
    "Sombre vert": {"fond": "#101b16", "carte": "#192820", "primaire": "#78b891", "accent": "#243d30", "texte": "#edf7f0", "bordure": "#345443"},
    "Sombre orange": {"fond": "#211710", "carte": "#302219", "primaire": "#dd9461", "accent": "#493022", "texte": "#fff5ed", "bordure": "#64422e"},
    "Sombre bleu": {"fond": "#101a24", "carte": "#182735", "primaire": "#70a9d2", "accent": "#233b50", "texte": "#eef7fd", "bordure": "#31546f"},
    "Sombre gris": {"fond": "#17191b", "carte": "#24272a", "primaire": "#a8b0b7", "accent": "#34383c", "texte": "#f3f4f5", "bordure": "#464b50"},
    "Sombre violet": {"fond": "#1c1521", "carte": "#2b2032", "primaire": "#b18ac8", "accent": "#412f4c", "texte": "#faf2ff", "bordure": "#5a4069"},
    "Sombre doré": {"fond": "#1d1a12", "carte": "#2c271a", "primaire": "#c8a84f", "accent": "#453b20", "texte": "#fff9e8", "bordure": "#63552d"},
}


def appliquer_theme(nom: str) -> None:
    couleurs = THEMES.get(nom, THEMES["Vert pastel"])
    sombre = nom.startswith("Sombre")
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {couleurs['fond']}; color: {couleurs['texte']}; }}
        [data-testid="stSidebar"] {{ background: {couleurs['carte']}; }}
        [data-testid="stMetric"], div[data-testid="stForm"], .budget-card {{
            background: {couleurs['carte']}; border: 1px solid {couleurs['bordure']};
            border-radius: 14px; padding: 1rem;
        }}
        .budget-card {{ min-height: 145px; margin-bottom: .75rem; }}
        .budget-card h3 {{ color: {couleurs['primaire']}; margin-top: 0; }}
        h1, h2, h3, p, label, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: {couleurs['texte']};
        }}
        .stButton > button, .stFormSubmitButton > button {{
            min-height: 2.75rem; border-radius: 10px; border-color: {couleurs['primaire']};
        }}
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
            background: {couleurs['primaire']}; color: {'#161616' if sombre else '#ffffff'};
        }}
        div[role="radiogroup"] label {{ padding: .35rem 0; font-size: 1.02rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

