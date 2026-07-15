from datetime import date
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.navigation import recharger_page
from src.services.budget_service import mois_budget_disponibles
from src.services.tableau_de_bord_service import (
    alertes_budget,
    comparaison_categories,
    comparaison_mois_precedent,
    depenses_cumulees,
    historique_mensuel,
    indicateurs,
    phrases_comparatif,
)
from src.services.transactions_service import mois_disponibles
from src.ui_styles import (
    carte_kpi,
    couleurs_actives,
    hauteur_graphique,
    styliser_graphique,
)
from src.utils import euros, libelle_mois, mois_canonique


def _graphique_suivi(
    mois: str, couleurs: dict[str, str], hauteur: int
) -> go.Figure:
    donnees = pd.DataFrame(depenses_cumulees(mois))
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=donnees["jour"], y=donnees["budget_theorique"],
            mode="lines", name="Budget théorique",
            line={"color": couleurs["couleur_graphique_2"], "width": 2, "dash": "dash"},
            hovertemplate="Jour %{x}<br>Budget théorique : %{y:,.2f} €<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=donnees["jour"], y=donnees["depenses_cumulees"],
            mode="lines+markers", name="Dépenses réelles",
            connectgaps=False,
            line={"color": couleurs["couleur_graphique_1"], "width": 3},
            marker={"size": 6},
            hovertemplate="Jour %{x}<br>Dépenses : %{y:,.2f} €<extra></extra>",
        )
    )
    if donnees["depenses_cumulees"].isna().all():
        figure.add_annotation(
            text="Aucune dépense enregistrée sur ce mois", x=.5, y=.5,
            xref="paper", yref="paper", showarrow=False,
            font={"color": couleurs["couleur_texte_secondaire"]},
        )
    figure.update_xaxes(dtick=1, title="Jour du mois")
    figure.update_yaxes(title="Montant cumulé")
    return styliser_graphique(
        figure, couleurs, "Évolution des dépenses cumulées", ",.0f €", hauteur
    )


def _graphique_historique(
    choix: str, historique: pd.DataFrame, couleurs: dict[str, str], hauteur: int
) -> go.Figure:
    figure = go.Figure()
    if historique.empty:
        figure.add_annotation(
            text="Aucune donnée mensuelle disponible", x=.5, y=.5,
            xref="paper", yref="paper", showarrow=False,
        )
        return styliser_graphique(figure, couleurs, hauteur=hauteur)
    if choix == "Dépenses par mois":
        figure.add_trace(
            go.Bar(
                x=historique["libelle_mois"], y=historique["depenses"],
                name="Dépenses", marker_color=couleurs["couleur_graphique_1"],
                hovertemplate="%{x}<br>%{y:,.2f} €<extra></extra>",
            )
        )
        titre, format_y = "Dépenses totales par mois budget", ",.0f €"
    elif choix == "Équilibre mensuel":
        series = [
            ("Revenus", "revenus", couleurs["couleur_positive"]),
            ("Dépenses", "depenses", couleurs["couleur_graphique_2"]),
            ("Épargne nette", "epargne_nette", couleurs["couleur_graphique_3"]),
        ]
        for nom, colonne, couleur in series:
            figure.add_trace(
                go.Bar(
                    x=historique["libelle_mois"], y=historique[colonne],
                    name=nom, marker_color=couleur,
                    hovertemplate=f"%{{x}}<br>{nom} : %{{y:,.2f}} €<extra></extra>",
                )
            )
        figure.update_layout(barmode="group")
        titre, format_y = "Revenus, dépenses et épargne nette", ",.0f €"
    elif choix == "Évolution du solde d’épargne":
        figure.add_trace(
            go.Scatter(
                x=historique["libelle_mois"], y=historique["solde_epargne"],
                mode="lines+markers", name="Solde d’épargne",
                fill="tozeroy",
                line={"color": couleurs["couleur_graphique_1"], "width": 3},
                fillcolor=couleurs["couleur_bloc"],
                marker={"size": 7},
                hovertemplate="%{x}<br>Solde : %{y:,.2f} €<extra></extra>",
            )
        )
        titre, format_y = "Évolution du solde d’épargne", ",.0f €"
    else:
        figure.add_trace(
            go.Scatter(
                x=historique["libelle_mois"], y=historique["taux_epargne"] * 100,
                mode="lines+markers", name="Taux d’épargne",
                line={"color": couleurs["couleur_graphique_3"], "width": 3},
                marker={"size": 7},
                hovertemplate="%{x}<br>%{y:.1f} %<extra></extra>",
            )
        )
        titre, format_y = "Taux d’épargne par mois", ".0f %"
    return styliser_graphique(figure, couleurs, titre, format_y, hauteur)


def _afficher_comparatif(mois: str) -> None:
    comparatif = comparaison_mois_precedent(mois)
    if not comparatif["disponible"]:
        st.markdown(
            '<section class="dashboard-panel"><h3>Comparatif M-1</h3>'
            '<p class="dashboard-empty">Pas encore de données pour M-1.</p></section>',
            unsafe_allow_html=True,
        )
        return
    noms = [
        ("Revenus", "revenus", "monnaie"),
        ("Dépenses", "depenses", "monnaie"),
        ("Épargne nette", "epargne_nette", "monnaie"),
        ("Reste disponible", "reste_disponible", "monnaie"),
        ("Taux d’épargne", "taux_epargne", "pourcentage"),
    ]
    lignes = []
    for libelle, cle, format_valeur in noms:
        if format_valeur == "pourcentage":
            courant = f"{comparatif['courant'][cle]:.1%}"
            precedent = f"{comparatif['precedent'][cle]:.1%}"
            ecart = f"{comparatif['ecarts'][cle] * 100:+.1f} point(s)"
        else:
            courant = euros(comparatif["courant"][cle])
            precedent = euros(comparatif["precedent"][cle])
            ecart = euros(comparatif["ecarts"][cle])
        lignes.append((libelle, courant, precedent, ecart))
    corps = "".join(
        "<tr>"
        f"<th>{escape(libelle)}</th><td>{escape(courant)}</td>"
        f"<td>{escape(precedent)}</td><td>{escape(ecart)}</td>"
        "</tr>"
        for libelle, courant, precedent, ecart in lignes
    )
    phrases = phrases_comparatif(comparatif)
    synthese = escape(phrases[0]) if phrases else ""
    st.markdown(
        '<section class="dashboard-panel comparison-panel">'
        '<h3>Comparatif M-1</h3><table class="comparison-table">'
        f'<thead><tr><th></th><th>{escape(libelle_mois(mois))}</th>'
        f'<th>{escape(libelle_mois(comparatif["mois_precedent"]))}</th><th>Écart</th></tr></thead>'
        f'<tbody>{corps}</tbody></table><p class="panel-note">{synthese}</p></section>',
        unsafe_allow_html=True,
    )


def _afficher_alertes(
    mois: str, seuil_vigilance: float, seuil_alerte: float
) -> None:
    donnees_categories = {
        ligne["categorie"]: ligne for ligne in comparaison_categories(mois)
    }
    elements = []
    alertes = alertes_budget(mois, seuil_vigilance, seuil_alerte)
    for alerte in alertes[:6]:
        categorie = alerte.get("categorie")
        ligne = donnees_categories.get(categorie, {})
        if alerte["type"] == "depassement":
            message = f"{categorie} : +{euros(float(ligne.get('reel', 0)) - float(ligne.get('budget_prevu', 0)))} vs budget"
        elif alerte["type"] == "vigilance":
            prevu = float(ligne.get("budget_prevu", 0))
            ratio = float(ligne.get("reel", 0)) / prevu if prevu else 0
            message = f"{categorie} : {ratio:.0%} utilisé"
        elif alerte["type"] == "aucun_budget":
            message = f"{categorie} : dépense sans budget"
        elif alerte["type"] == "reste_negatif":
            message = "Reste disponible négatif"
        elif alerte["type"] == "aucune":
            message = "Aucune alerte budget"
        else:
            message = alerte["message"]
        classe = "ok" if alerte["niveau"] == "ok" else (
            "warning" if alerte["niveau"] == "vigilance" else "danger"
        )
        elements.append(
            f'<li class="alert-{classe}"><span></span>{escape(message)}</li>'
        )
    if len(alertes) > 6:
        elements.append(f'<li class="alert-more">+{len(alertes) - 6} autre(s)</li>')
    st.markdown(
        '<section class="dashboard-panel alerts-panel"><h3>Alertes budget</h3>'
        f'<ul class="compact-alerts">{"".join(elements)}</ul></section>',
        unsafe_allow_html=True,
    )


def _afficher_budget_categories(
    mois: str, couleurs: dict[str, str], colonnes: int
) -> None:
    comparaison = comparaison_categories(mois)
    if not comparaison:
        st.markdown(
            '<section class="budget-excel"><h3>Budget prévu vs réel</h3>'
            '<p class="dashboard-empty">Aucune catégorie à comparer.</p></section>',
            unsafe_allow_html=True,
        )
        return
    cartes = []
    for ligne in comparaison:
        prevu = max(0.0, float(ligne["budget_prevu"]))
        reel = float(ligne["reel"])
        reel_barre = max(0.0, reel)
        maximum = max(prevu, reel_barre, 1.0)
        largeur_prevu = min(100.0, prevu / maximum * 100)
        largeur_reel = min(100.0, reel_barre / maximum * 100)
        ratio = reel / prevu if prevu > 0 else None
        pourcentage = f"{ratio:.0%}" if ratio is not None else "Sans budget"
        couleur_reel = (
            couleurs["couleur_negative"]
            if ligne["depassement"] else couleurs["couleur_positive"]
        )
        cartes.append(
            '<article class="budget-category">'
            f'<header><strong>{escape(str(ligne["categorie"]))}</strong>'
            f'<span class="category-ratio">{escape(pourcentage)}</span></header>'
            '<div class="budget-row"><span>Prévu</span><div class="bar-track">'
            f'<i style="width:{largeur_prevu:.1f}%;background:{couleurs["couleur_graphique_2"]}"></i>'
            f'</div><b>{escape(euros(prevu))}</b></div>'
            '<div class="budget-row"><span>Réel</span><div class="bar-track">'
            f'<i style="width:{largeur_reel:.1f}%;background:{couleur_reel}"></i>'
            f'</div><b style="color:{couleur_reel}">{escape(euros(reel))}</b></div>'
            '</article>'
        )
    st.markdown(
        '<section class="budget-excel"><h3>Budget prévu vs dépenses réelles</h3>'
        f'<div class="budget-excel-grid cols-{colonnes}">{"".join(cartes)}</div></section>',
        unsafe_allow_html=True,
    )


def afficher(parametres: dict) -> None:
    couleurs = couleurs_actives(parametres)
    hauteur_principale = hauteur_graphique(parametres)
    mode_27_pouces = parametres.get("configuration_affichage") == "ecran_27"
    colonnes_budget = 4 if mode_27_pouces else 3
    st.markdown(
        """<style>
        .block-container { max-width: 1900px; padding: .3rem .7rem .55rem; }
        [data-testid="stVerticalBlock"] { gap: .32rem; }
        [data-testid="stHorizontalBlock"] { gap: .5rem; }
        .dashboard-title {
            width: 100%; margin: .15rem 0 .35rem !important;
            text-align: center; font-size: 1.72rem !important;
            line-height: 1.15; letter-spacing: -.025em;
        }
        .kpi-card { min-height: 67px; padding: .48rem .62rem; border-radius: 10px; }
        .kpi-card::after { height: 3px; }
        .kpi-title { margin-bottom: .18rem; font-size: .78rem; white-space: nowrap; }
        .kpi-value { font-size: 1.12rem; }
        .dashboard-panel, .budget-excel {
            background: var(--app-carte); border: 1px solid var(--app-bordure);
            border-radius: 10px; padding: .42rem .55rem;
        }
        .dashboard-panel h3, .budget-excel h3 {
            font-size: .9rem !important; margin: 0 0 .28rem !important;
            color: var(--app-principale);
        }
        .comparison-table { width: 100%; border-collapse: collapse; font-size: .69rem; }
        .comparison-table th, .comparison-table td {
            padding: .14rem .2rem; border-bottom: 1px solid var(--app-bordure);
            text-align: right; white-space: nowrap;
        }
        .comparison-table th:first-child { text-align: left; }
        .comparison-table thead th { color: var(--app-texte-secondaire); font-weight: 600; }
        .panel-note, .dashboard-empty {
            color: var(--app-texte-secondaire); font-size: .68rem; line-height: 1.2;
            margin: .25rem 0 0;
        }
        .alerts-panel { margin-top: .75rem; }
        .compact-alerts { list-style: none; margin: 0; padding: 0; }
        .compact-alerts li {
            display: flex; align-items: center; gap: .35rem; font-size: .72rem;
            line-height: 1.2; padding: .12rem 0; color: var(--app-texte);
        }
        .compact-alerts li span { width: .42rem; height: .42rem; border-radius: 50%; flex: none; }
        .compact-alerts .alert-ok span { background: var(--app-positive); }
        .compact-alerts .alert-warning span { background: var(--app-vigilance); }
        .compact-alerts .alert-danger span { background: var(--app-negative); }
        .compact-alerts .alert-more { color: var(--app-texte-secondaire); }
        .budget-excel { padding-bottom: .5rem; }
        .budget-excel-grid {
            display: grid; gap: .38rem; grid-template-columns: repeat(4, minmax(0, 1fr));
        }
        .budget-excel-grid.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .budget-category {
            background: var(--app-bloc); border: 1px solid var(--app-bordure);
            border-radius: 8px; padding: .3rem .4rem;
        }
        .budget-category header {
            display: flex; justify-content: space-between; gap: .4rem;
            font-size: .75rem; margin-bottom: .18rem;
        }
        .category-ratio { color: var(--app-principale); font-weight: 700; white-space: nowrap; }
        .budget-row {
            display: grid; grid-template-columns: 2.6rem minmax(35px, 1fr) 4.7rem;
            align-items: center; gap: .25rem; font-size: .66rem; line-height: 1.35;
        }
        .budget-row b { text-align: right; white-space: nowrap; font-weight: 650; }
        .bar-track { height: .38rem; border-radius: 999px; background: var(--app-carte); overflow: hidden; }
        .bar-track i { display: block; height: 100%; border-radius: inherit; }
        @media (max-width: 1200px) {
            .budget-excel-grid, .budget-excel-grid.cols-3 {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>""",
        unsafe_allow_html=True,
    )
    if mode_27_pouces:
        st.markdown(
            """<style>
            .block-container { padding-top: .52rem; padding-bottom: .75rem; }
            [data-testid="stVerticalBlock"] { gap: .7rem; }
            [data-testid="stHorizontalBlock"] { gap: .62rem; }
            .dashboard-title { margin-bottom: .62rem !important; }
            .kpi-card { min-height: 72px; padding: .55rem .65rem; }
            .dashboard-panel, .budget-excel { padding: .55rem .65rem; }
            .alerts-panel { margin-top: 1rem; }
            .budget-excel { margin-top: .12rem; }
            .budget-excel-grid { gap: .5rem; }
            </style>""",
            unsafe_allow_html=True,
        )
    mois = sorted(set(mois_budget_disponibles()) | set(mois_disponibles()))
    if not mois:
        mois = [mois_canonique(date.today())]
    if st.session_state.get("mois_tableau_de_bord") not in mois:
        st.session_state["mois_tableau_de_bord"] = mois[-1]
    col_commandes, col_titre, _ = st.columns(
        [1.25, 3.5, 1.25], vertical_alignment="top"
    )
    with col_commandes:
        if st.button("Actualiser", width="stretch"):
            recharger_page("Tableau de bord")
        selection = st.selectbox(
            "Mois budget", mois, format_func=libelle_mois,
            key="mois_tableau_de_bord",
        )
    with col_titre:
        st.markdown(
            '<h1 class="dashboard-title">Tableau de bord</h1>',
            unsafe_allow_html=True,
        )

    kpi = indicateurs(selection)
    colonnes = st.columns(6, gap="small")
    cartes = [
        ("Revenus du mois", euros(kpi["revenus"]), couleurs["couleur_positive"]),
        ("Budget du mois", euros(kpi["budget_depenses"]), couleurs["couleur_secondaire"]),
        ("Dépenses du mois", euros(kpi["depenses"]), couleurs["couleur_graphique_2"]),
        ("Reste disponible", euros(kpi["reste_disponible"]), couleurs["couleur_positive"] if kpi["reste_disponible"] >= 0 else couleurs["couleur_negative"]),
        ("Épargne nette", euros(kpi["epargne_nette"]), couleurs["couleur_positive"] if kpi["epargne_nette"] >= 0 else couleurs["couleur_negative"]),
        ("Taux d’épargne", f"{kpi['taux_epargne']:.1%}", couleurs["couleur_graphique_3"]),
    ]
    for colonne, (titre, valeur, couleur) in zip(colonnes, cartes):
        carte_kpi(colonne, titre, valeur, couleur)

    historique = pd.DataFrame(
        historique_mensuel(float(parametres.get("solde_initial_epargne", 0)))
    )
    if not historique.empty:
        historique["libelle_mois"] = historique["mois"].map(libelle_mois)
    seuil_vigilance = float(parametres.get("seuil_vigilance_budget", 0.8))
    seuil_alerte = float(parametres.get("seuil_alerte_budget", 1.0))
    col_graphique, col_infos = st.columns([2.15, 1], gap="medium")
    with col_graphique:
        choix = st.selectbox(
            "Graphique principal",
            [
                "Évolution des dépenses cumulées du mois",
                "Dépenses par mois",
                "Équilibre mensuel",
                "Taux d’épargne par mois",
                "Évolution du solde d’épargne",
            ],
        )
        figure = (
            _graphique_suivi(selection, couleurs, hauteur_principale)
            if choix == "Évolution des dépenses cumulées du mois"
            else _graphique_historique(choix, historique, couleurs, hauteur_principale)
        )
        st.plotly_chart(figure, width="stretch", key=f"graphique_principal_{choix}")
    with col_infos:
        _afficher_comparatif(selection)
        _afficher_alertes(selection, seuil_vigilance, seuil_alerte)

    _afficher_budget_categories(selection, couleurs, colonnes_budget)
