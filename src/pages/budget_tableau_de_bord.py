from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.services.budget_service import mois_budget_disponibles
from src.services.tableau_de_bord_service import (
    alertes_budget,
    comparaison_categories,
    comparaison_mois_precedent,
    depenses_cumulees,
    historique_mensuel,
    indicateurs,
    phrases_comparatif,
    resume_automatique,
)
from src.services.transactions_service import mois_disponibles
from src.ui_styles import bloc_resume, carte_kpi, couleurs_actives, styliser_graphique
from src.utils import euros, libelle_mois, mois_canonique


def _graphique_suivi(mois: str, couleurs: dict[str, str]) -> go.Figure:
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
        figure, couleurs, "Évolution des dépenses cumulées", ",.0f €"
    )


def _graphique_historique(
    choix: str, historique: pd.DataFrame, couleurs: dict[str, str]
) -> go.Figure:
    figure = go.Figure()
    if historique.empty:
        figure.add_annotation(
            text="Aucune donnée mensuelle disponible", x=.5, y=.5,
            xref="paper", yref="paper", showarrow=False,
        )
        return styliser_graphique(figure, couleurs)
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
    return styliser_graphique(figure, couleurs, titre, format_y)


def _afficher_comparatif(mois: str) -> None:
    comparatif = comparaison_mois_precedent(mois)
    st.subheader("Comparatif M-1")
    if not comparatif["disponible"]:
        st.info("Pas encore de données pour le mois précédent.")
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
        evolution = comparatif["evolutions"][cle]
        if format_valeur == "pourcentage":
            courant = f"{comparatif['courant'][cle]:.1%}"
            precedent = f"{comparatif['precedent'][cle]:.1%}"
            ecart = f"{comparatif['ecarts'][cle] * 100:+.1f} point(s)"
        else:
            courant = euros(comparatif["courant"][cle])
            precedent = euros(comparatif["precedent"][cle])
            ecart = euros(comparatif["ecarts"][cle])
        lignes.append(
            {
                "Indicateur": libelle,
                libelle_mois(mois): courant,
                libelle_mois(comparatif["mois_precedent"]): precedent,
                "Écart": ecart,
                "Évolution": "—" if evolution is None else f"{evolution:+.1%}",
            }
        )
    st.dataframe(pd.DataFrame(lignes), hide_index=True, width="stretch")
    for phrase in phrases_comparatif(comparatif):
        st.caption(phrase)


def _afficher_alertes(
    mois: str, seuil_vigilance: float, seuil_alerte: float
) -> None:
    st.subheader("Alertes budget")
    for alerte in alertes_budget(mois, seuil_vigilance, seuil_alerte):
        if alerte["niveau"] == "ok":
            st.success(alerte["message"])
        elif alerte["niveau"] == "vigilance":
            st.warning(alerte["message"])
        else:
            st.error(alerte["message"])


def _graphique_categories(mois: str, couleurs: dict[str, str]) -> go.Figure | None:
    comparaison = comparaison_categories(mois)
    if not comparaison:
        return None
    categories = [ligne["categorie"] for ligne in comparaison]
    prevus = [ligne["budget_prevu"] for ligne in comparaison]
    reels = [ligne["reel"] for ligne in comparaison]
    couleurs_reelles = [
        couleurs["couleur_negative"] if ligne["depassement"] else couleurs["couleur_positive"]
        for ligne in comparaison
    ]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=categories, y=prevus, name="Budget prévu",
            marker_color=couleurs["couleur_graphique_2"],
            hovertemplate="%{x}<br>Prévu : %{y:,.2f} €<extra></extra>",
        )
    )
    figure.add_trace(
        go.Bar(
            x=categories, y=reels, name="Dépenses réelles",
            marker_color=couleurs_reelles,
            hovertemplate="%{x}<br>Réel : %{y:,.2f} €<extra></extra>",
        )
    )
    figure.update_layout(barmode="group")
    return styliser_graphique(
        figure, couleurs,
        "Budget prévu vs dépenses réelles par catégorie", ",.0f €",
    )


def afficher(parametres: dict) -> None:
    couleurs = couleurs_actives(parametres)
    st.title("Tableau de bord")
    mois = sorted(set(mois_budget_disponibles()) | set(mois_disponibles()))
    if not mois:
        mois = [mois_canonique(date.today())]
    col_mois, col_actualiser = st.columns([4, 1])
    selection = col_mois.selectbox(
        "Mois budget", mois, index=len(mois) - 1, format_func=libelle_mois
    )
    if col_actualiser.button("Actualiser", width="stretch"):
        st.rerun()

    kpi = indicateurs(selection)
    colonnes = st.columns(6, gap="small")
    cartes = [
        ("Revenus du mois", euros(kpi["revenus"]), couleurs["couleur_positive"], "Revenus réalisés"),
        ("Budget du mois", euros(kpi["budget_depenses"]), couleurs["couleur_secondaire"], "Dépenses prévues"),
        ("Dépenses du mois", euros(kpi["depenses"]), couleurs["couleur_graphique_2"], "Remboursements inclus"),
        ("Reste disponible", euros(kpi["reste_disponible"]), couleurs["couleur_positive"] if kpi["reste_disponible"] >= 0 else couleurs["couleur_negative"], "Après dépenses et épargne"),
        ("Épargne nette", euros(kpi["epargne_nette"]), couleurs["couleur_positive"] if kpi["epargne_nette"] >= 0 else couleurs["couleur_negative"], "Versements moins retraits"),
        ("Taux d’épargne", f"{kpi['taux_epargne']:.1%}", couleurs["couleur_graphique_3"], "Sur les revenus du mois"),
    ]
    for colonne, (titre, valeur, couleur, detail) in zip(colonnes, cartes):
        carte_kpi(colonne, titre, valeur, couleur, detail)

    st.subheader("Analyse graphique")
    choix = st.radio(
        "Vue graphique",
        ["Suivi du mois", "Dépenses par mois", "Équilibre mensuel", "Taux d’épargne"],
        horizontal=True,
        label_visibility="collapsed",
    )
    historique = pd.DataFrame(
        historique_mensuel(float(parametres.get("solde_initial_epargne", 0)))
    )
    if not historique.empty:
        historique["libelle_mois"] = historique["mois"].map(libelle_mois)
    with st.container(border=True):
        figure = (
            _graphique_suivi(selection, couleurs)
            if choix == "Suivi du mois"
            else _graphique_historique(choix, historique, couleurs)
        )
        st.plotly_chart(figure, width="stretch", key=f"graphique_principal_{choix}")

    seuil_vigilance = float(parametres.get("seuil_vigilance_budget", 0.8))
    seuil_alerte = float(parametres.get("seuil_alerte_budget", 1.0))
    col_comparatif, col_alertes = st.columns(2, gap="large")
    with col_comparatif:
        _afficher_comparatif(selection)
    with col_alertes:
        _afficher_alertes(selection, seuil_vigilance, seuil_alerte)

    st.subheader("Résumé du mois")
    bloc_resume(resume_automatique(selection, seuil_vigilance, seuil_alerte))

    st.subheader("Détail par catégorie")
    graphique_categories = _graphique_categories(selection, couleurs)
    if graphique_categories is None:
        st.info("Créez le budget du mois ou ajoutez des dépenses pour afficher cette comparaison.")
    else:
        st.plotly_chart(graphique_categories, width="stretch", key="graphique_categories")
