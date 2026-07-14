import streamlit as st


def _theme(
    fond: str, carte: str, bloc: str, principale: str, secondaire: str,
    bouton: str, bouton_selection: str, texte: str, texte_secondaire: str,
    texte_inverse: str, bordure: str, positive: str, negative: str,
    vigilance: str, graphique_1: str, graphique_2: str, graphique_3: str,
) -> dict[str, str]:
    return {
        "couleur_fond": fond,
        "couleur_carte": carte,
        "couleur_bloc": bloc,
        "couleur_principale": principale,
        "couleur_secondaire": secondaire,
        "couleur_bouton": bouton,
        "couleur_bouton_selection": bouton_selection,
        "couleur_texte": texte,
        "couleur_texte_secondaire": texte_secondaire,
        "couleur_texte_inverse": texte_inverse,
        "couleur_bordure": bordure,
        "couleur_positive": positive,
        "couleur_negative": negative,
        "couleur_vigilance": vigilance,
        "couleur_graphique_1": graphique_1,
        "couleur_graphique_2": graphique_2,
        "couleur_graphique_3": graphique_3,
    }


THEMES = {
    "Vert pastel": _theme(
        "#f3f8f4", "#ffffff", "#eaf4ed", "#397356", "#7da88d",
        "#397356", "#285c42", "#183228", "#617269", "#ffffff",
        "#c9ddd0", "#2f8a5b", "#c84f56", "#d28a2f", "#397356", "#77a98b", "#d7a34b",
    ),
    "Orange pastel": _theme(
        "#fff7ef", "#ffffff", "#fceddf", "#b9632f", "#d99a69",
        "#b9632f", "#93471f", "#452819", "#806353", "#ffffff",
        "#efd0b6", "#3f8b61", "#c54e50", "#d18428", "#b9632f", "#e39b61", "#647fa5",
    ),
    "Bleu pastel": _theme(
        "#f2f7fb", "#ffffff", "#e5f0f7", "#3c7398", "#7aa7c3",
        "#3c7398", "#285c7e", "#173448", "#607482", "#ffffff",
        "#c5dceb", "#39845c", "#c44f5b", "#cf8a2d", "#3c7398", "#76a7c7", "#8b76b5",
    ),
    "Gris pastel": _theme(
        "#f5f6f7", "#ffffff", "#e9ecef", "#606d77", "#98a2aa",
        "#606d77", "#45515b", "#272f35", "#6d767d", "#ffffff",
        "#d2d7db", "#38815a", "#bd4d55", "#c8842d", "#606d77", "#929da5", "#8a74aa",
    ),
    "Violet pastel": _theme(
        "#faf5fc", "#ffffff", "#f0e6f4", "#7c5892", "#ae8ebf",
        "#7c5892", "#623f78", "#3a2546", "#74627d", "#ffffff",
        "#ddcbe6", "#38815a", "#c14f64", "#cb872d", "#7c5892", "#b58bc5", "#4e86a3",
    ),
    "Sombre vert": _theme(
        "#0d1712", "#16241c", "#203329", "#79c398", "#4d8a68",
        "#67b286", "#86cfa3", "#f1f8f3", "#aabdb0", "#102018",
        "#355442", "#67cf91", "#ff7b83", "#f2b65a", "#79c398", "#65a8d0", "#e2a957",
    ),
    "Sombre orange": _theme(
        "#1c130d", "#2a1e16", "#3b2a1e", "#e39b68", "#a96943",
        "#cf8453", "#eba976", "#fff5ed", "#c8b0a0", "#21140c",
        "#5c402d", "#70d39a", "#ff7e83", "#f5ba5d", "#e39b68", "#7fa9d1", "#b18bd0",
    ),
    "Sombre bleu": _theme(
        "#0c1620", "#152431", "#203545", "#72b2df", "#477fa5",
        "#5b9bc7", "#80bee8", "#eef8ff", "#a9bdca", "#0d1922",
        "#31546c", "#6bd19a", "#ff7e8b", "#f2b75c", "#72b2df", "#8a8fd0", "#e1a857",
    ),
    "Sombre gris": _theme(
        "#141618", "#202326", "#2d3135", "#b2bbc2", "#737d85",
        "#8d989f", "#bcc4ca", "#f5f6f7", "#b1b6ba", "#171a1c",
        "#464c51", "#69cc94", "#ff7d84", "#efb257", "#aeb8bf", "#6ca8cd", "#bd8dce",
    ),
    "Sombre violet": _theme(
        "#18111d", "#271b2d", "#382640", "#bb8ed2", "#815a94",
        "#a474ba", "#c699dc", "#fbf3ff", "#c2abc9", "#1b1120",
        "#583c63", "#6ed09a", "#ff7c91", "#f0b45a", "#bb8ed2", "#6ea9d1", "#e1a956",
    ),
    "Sombre doré": _theme(
        "#19160e", "#272218", "#37301f", "#d5b45a", "#927b3c",
        "#b99a48", "#ddc16d", "#fff9e9", "#c5bda7", "#1c180e",
        "#574b2a", "#70cf97", "#ff7e82", "#efb54f", "#d5b45a", "#75a9cb", "#b68bc8",
    ),
}


def obtenir_theme(nom: str | None) -> dict[str, str]:
    return THEMES.get(nom or "", THEMES["Vert pastel"])


def appliquer_theme(nom: str) -> None:
    c = obtenir_theme(nom)
    sombre = nom.startswith("Sombre")
    st.markdown(
        f"""
        <style>
        :root {{
            --app-fond: {c['couleur_fond']};
            --app-carte: {c['couleur_carte']};
            --app-bloc: {c['couleur_bloc']};
            --app-principale: {c['couleur_principale']};
            --app-texte: {c['couleur_texte']};
            --app-texte-secondaire: {c['couleur_texte_secondaire']};
            --app-bordure: {c['couleur_bordure']};
            --app-positive: {c['couleur_positive']};
            --app-negative: {c['couleur_negative']};
            --app-vigilance: {c['couleur_vigilance']};
        }}
        html, body, [class*="css"] {{ font-size: 16px; }}
        .stApp {{ background: var(--app-fond); color: var(--app-texte); }}
        .block-container {{ max-width: 1540px; padding-top: 1.6rem; padding-bottom: 3rem; }}
        [data-testid="stSidebar"] {{
            background: {c['couleur_carte']};
            border-right: 1px solid var(--app-bordure);
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: var(--app-texte-secondaire);
        }}
        h1 {{ font-size: 2rem !important; letter-spacing: -.025em; margin-bottom: .75rem !important; }}
        h2 {{ font-size: 1.42rem !important; margin-top: 1.7rem !important; }}
        h3 {{ font-size: 1.12rem !important; }}
        h1, h2, h3, p, label, span, [data-testid="stCaptionContainer"] {{ color: var(--app-texte); }}
        [data-testid="stCaptionContainer"], small {{ color: var(--app-texte-secondaire) !important; }}
        [data-testid="stMetric"], div[data-testid="stForm"], .budget-card,
        .app-panel, .kpi-card, .summary-card {{
            background: var(--app-carte);
            border: 1px solid var(--app-bordure);
            border-radius: 15px;
            box-shadow: {'0 8px 24px rgba(0,0,0,.18)' if sombre else '0 5px 18px rgba(35,55,45,.06)'};
        }}
        [data-testid="stMetric"] {{ padding: 1rem 1.1rem; }}
        [data-testid="stMetricLabel"] {{ color: var(--app-texte-secondaire) !important; font-size: .92rem; }}
        [data-testid="stMetricValue"] {{ color: var(--app-texte) !important; font-weight: 750; }}
        .budget-card {{ min-height: 145px; margin-bottom: .75rem; padding: 1rem; }}
        .budget-card h3 {{ color: var(--app-principale); margin-top: 0; }}
        .app-panel {{ padding: 1rem 1.15rem; margin: .4rem 0 1rem; }}
        .summary-card {{ padding: 1rem 1.2rem; border-left: 5px solid var(--app-principale); }}
        .kpi-card {{ min-height: 118px; padding: 1rem; position: relative; overflow: hidden; }}
        .kpi-card::after {{ content: ''; position: absolute; left: 0; bottom: 0; width: 100%; height: 4px; background: var(--kpi-color); }}
        .kpi-title {{ color: var(--app-texte-secondaire); font-size: .88rem; font-weight: 650; margin-bottom: .55rem; }}
        .kpi-value {{ color: var(--app-texte); font-size: 1.45rem; font-weight: 780; line-height: 1.15; }}
        .kpi-detail {{ color: var(--app-texte-secondaire); font-size: .78rem; margin-top: .45rem; }}
        .stButton > button, .stFormSubmitButton > button, [data-testid="stDownloadButton"] > button {{
            min-height: 2.8rem; border-radius: 10px; border: 1px solid {c['couleur_bouton']};
            padding: .55rem 1rem; font-weight: 650;
        }}
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
            background: {c['couleur_bouton']}; color: {c['couleur_texte_inverse']};
        }}
        .stButton > button[kind="primary"] p, .stButton > button[kind="primary"] span,
        .stFormSubmitButton > button[kind="primary"] p,
        .stFormSubmitButton > button[kind="primary"] span {{
            color: {c['couleur_texte_inverse']} !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            border-color: {c['couleur_bouton_selection']}; color: {c['couleur_bouton_selection']};
        }}
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {{
            background: {c['couleur_bouton_selection']}; color: {c['couleur_texte_inverse']};
        }}
        div[role="radiogroup"] {{ gap: .35rem; }}
        div[role="radiogroup"] label {{ padding: .45rem .65rem; font-size: 1rem; }}
        [data-baseweb="select"] > div, [data-baseweb="input"] > div,
        [data-baseweb="base-input"], textarea {{
            background: {c['couleur_carte']} !important;
            color: var(--app-texte) !important;
            border-color: var(--app-bordure) !important;
        }}
        input, textarea, [data-baseweb="select"] span {{ color: var(--app-texte) !important; }}
        [data-baseweb="popover"], [role="listbox"], [role="option"] {{
            background: {c['couleur_carte']} !important; color: var(--app-texte) !important;
        }}
        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border: 1px solid var(--app-bordure); border-radius: 12px; overflow: hidden;
        }}
        [data-testid="stAlert"] {{ border-radius: 12px; }}
        hr {{ border-color: var(--app-bordure) !important; margin: 1.5rem 0 !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
