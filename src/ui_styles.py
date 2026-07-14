from html import escape

import plotly.graph_objects as go
import streamlit as st

from src.themes import obtenir_theme


def couleurs_actives(parametres: dict) -> dict[str, str]:
    return obtenir_theme(parametres.get("theme_actif", "Vert pastel"))


def carte_kpi(
    conteneur,
    titre: str,
    valeur: str,
    couleur: str,
    detail: str = "",
) -> None:
    conteneur.markdown(
        f"""<div class="kpi-card" style="--kpi-color:{escape(couleur)}">
        <div class="kpi-title">{escape(titre)}</div>
        <div class="kpi-value">{escape(valeur)}</div>
        <div class="kpi-detail">{escape(detail) if detail else '&nbsp;'}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def bloc_resume(phrases: list[str]) -> None:
    contenu = " ".join(escape(phrase) for phrase in phrases)
    st.markdown(
        f'<div class="summary-card"><strong>Résumé du mois</strong><br>{contenu}</div>',
        unsafe_allow_html=True,
    )


def styliser_graphique(
    figure: go.Figure,
    couleurs: dict[str, str],
    titre: str | None = None,
    format_axe_y: str | None = None,
) -> go.Figure:
    tickformat = format_axe_y
    ticksuffix = None
    if format_axe_y and "€" in format_axe_y:
        tickformat, ticksuffix = ",.0f", " €"
    elif format_axe_y and "%" in format_axe_y:
        tickformat, ticksuffix = ".0f", " %"
    figure.update_layout(
        title={"text": titre or "", "font": {"size": 17}},
        height=420,
        margin=dict(l=28, r=22, t=52 if titre else 28, b=38),
        paper_bgcolor=couleurs["couleur_carte"],
        plot_bgcolor=couleurs["couleur_bloc"],
        font={"color": couleurs["couleur_texte"], "size": 13},
        hoverlabel={
            "bgcolor": couleurs["couleur_carte"],
            "font_color": couleurs["couleur_texte"],
            "bordercolor": couleurs["couleur_bordure"],
        },
        legend={
            "orientation": "h", "yanchor": "bottom", "y": 1.02,
            "xanchor": "left", "x": 0,
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
