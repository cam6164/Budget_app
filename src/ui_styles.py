from html import escape

import plotly.graph_objects as go
import streamlit as st

from src.themes import obtenir_theme


def couleurs_actives(parametres: dict) -> dict[str, str]:
    return obtenir_theme(parametres.get("theme_actif", "Sombre bleu"))


CONFIGURATIONS_AFFICHAGE = {
    "ecran_15": {
        "chart_height": 240,
        "secondary_chart_height": 180,
        "table_height": 310,
        "preview_height": 185,
        "grid_height": 330,
    },
    "ecran_27": {
        "chart_height": 340,
        "secondary_chart_height": 210,
        "table_height": 520,
        "preview_height": 265,
        "grid_height": 520,
    },
}


def configuration_affichage(parametres: dict) -> dict[str, int]:
    nom = parametres.get("configuration_affichage", "ecran_15")
    return CONFIGURATIONS_AFFICHAGE.get(nom, CONFIGURATIONS_AFFICHAGE["ecran_15"])


def get_display_config(parametres: dict) -> dict[str, int]:
    return configuration_affichage(parametres)


def get_layout_sizes(parametres: dict) -> dict[str, int]:
    return configuration_affichage(parametres).copy()


def hauteur_graphique(parametres: dict, secondaire: bool = False) -> int:
    cle = "secondary_chart_height" if secondaire else "chart_height"
    return configuration_affichage(parametres)[cle]


def get_chart_height(parametres: dict, secondaire: bool = False) -> int:
    return hauteur_graphique(parametres, secondaire)


def hauteur_tableau(parametres: dict, grille: bool = False) -> int:
    cle = "grid_height" if grille else "table_height"
    return configuration_affichage(parametres)[cle]


def get_table_height(parametres: dict, grille: bool = False) -> int:
    return hauteur_tableau(parametres, grille)


def hauteur_apercu(parametres: dict) -> int:
    return configuration_affichage(parametres)["preview_height"]


def appliquer_configuration_affichage(parametres: dict) -> None:
    compact = parametres.get("configuration_affichage", "ecran_15") == "ecran_15"
    if not compact:
        return
    st.markdown(
        """
        <style>
        .block-container { padding-top: .65rem; padding-bottom: 1rem; }
        h1 { font-size: 1.65rem !important; margin: .1rem 0 .35rem !important; }
        h2 { font-size: 1.25rem !important; margin: .75rem 0 .35rem !important; }
        h3 { margin: .5rem 0 .25rem !important; }
        [data-testid="stVerticalBlock"] { gap: .55rem; }
        [data-testid="stHorizontalBlock"] { gap: .65rem; }
        [data-testid="stMetric"] { padding: .55rem .75rem; }
        [data-testid="stMetricValue"] { font-size: 1.35rem; }
        .kpi-card { min-height: 88px; padding: .65rem .75rem; }
        .kpi-title { margin-bottom: .25rem; }
        .kpi-value { font-size: 1.2rem; }
        .kpi-detail { margin-top: .2rem; }
        .app-panel { padding: .65rem .8rem; margin: .2rem 0 .45rem; }
        div[data-testid="stForm"] { padding: .75rem; }
        .stButton > button, .stFormSubmitButton > button,
        [data-testid="stDownloadButton"] > button { min-height: 2.35rem; padding: .35rem .75rem; }
        [data-testid="stAlert"] { padding: .5rem .75rem; }
        hr { margin: .65rem 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def carte_kpi(
    conteneur,
    titre: str,
    valeur: str,
    couleur: str,
    detail: str = "",
) -> None:
    detail_html = (
        f'<div class="kpi-detail">{escape(detail)}</div>' if detail else ""
    )
    html = (
        f'<div class="kpi-card" style="--kpi-color:{escape(couleur)}">'
        f'<div class="kpi-title">{escape(titre)}</div>'
        f'<div class="kpi-value">{escape(valeur)}</div>'
        f'{detail_html}</div>'
    )
    conteneur.markdown(html, unsafe_allow_html=True)


def styliser_graphique(
    figure: go.Figure,
    couleurs: dict[str, str],
    titre: str | None = None,
    format_axe_y: str | None = None,
    hauteur: int | None = None,
) -> go.Figure:
    tickformat = format_axe_y
    ticksuffix = None
    if format_axe_y and "€" in format_axe_y:
        tickformat, ticksuffix = ",.0f", " €"
    elif format_axe_y and "%" in format_axe_y:
        tickformat, ticksuffix = ".0f", " %"
    figure.update_layout(
        title={"text": titre or "", "font": {"size": 14}},
        height=hauteur or 420,
        margin=dict(l=20, r=10, t=34 if titre else 16, b=44),
        paper_bgcolor=couleurs["couleur_carte"],
        plot_bgcolor=couleurs["couleur_bloc"],
        font={"color": couleurs["couleur_texte"], "size": 13},
        hoverlabel={
            "bgcolor": couleurs["couleur_carte"],
            "font_color": couleurs["couleur_texte"],
            "bordercolor": couleurs["couleur_bordure"],
        },
        legend={
            "orientation": "h", "yanchor": "top", "y": -0.13,
            "xanchor": "right", "x": 1,
        },
        coloraxis_showscale=False,
    )
    figure.update_xaxes(
        showgrid=False,
        linecolor=couleurs["couleur_bordure"],
        tickfont={"color": couleurs["couleur_texte_secondaire"]},
        title_font={"color": couleurs["couleur_texte_secondaire"]},
    )
    figure.update_yaxes(
        gridcolor=couleurs["couleur_bordure"],
        zerolinecolor=couleurs["couleur_bordure"],
        tickfont={"color": couleurs["couleur_texte_secondaire"]},
        title_font={"color": couleurs["couleur_texte_secondaire"]},
        tickformat=tickformat,
        ticksuffix=ticksuffix,
    )
    return figure
