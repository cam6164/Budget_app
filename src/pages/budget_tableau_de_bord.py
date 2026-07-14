from datetime import date

import pandas as pd
import plotly.express as px
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
)
from src.services.transactions_service import mois_disponibles
from src.utils import euros, libelle_mois, mois_canonique


def _graphique_principal(choix: str, mois: str, historique: pd.DataFrame) -> go.Figure:
    if choix == "Évolution des dépenses cumulées du mois":
        donnees = pd.DataFrame(depenses_cumulees(mois))
        if donnees.empty:
            return go.Figure().update_layout(title="Aucune dépense sur ce mois")
        return px.line(donnees, x="jour", y="depenses_cumulees", markers=True, labels={"jour": "Jour", "depenses_cumulees": "Dépenses cumulées (€)"})
    if historique.empty:
        return go.Figure().update_layout(title="Aucune donnée disponible")
    if choix == "Dépenses par mois":
        return px.bar(historique, x="Mois", y="Dépenses", labels={"Dépenses": "Dépenses (€)"})
    if choix == "Équilibre mensuel":
        return px.bar(historique, x="Mois", y="Équilibre", color="Équilibre", color_continuous_scale="RdYlGn")
    return px.line(historique, x="Mois", y="Taux d’épargne", markers=True, labels={"Taux d’épargne": "Taux d’épargne"})


def afficher(parametres: dict) -> None:
    st.title("Tableau de bord")
    mois = sorted(set(mois_budget_disponibles()) | set(mois_disponibles()))
    if not mois:
        mois = [mois_canonique(date.today())]
    selection = st.selectbox("Mois budget", mois, index=len(mois) - 1, format_func=libelle_mois)
    kpi = indicateurs(selection)
    colonnes = st.columns(6)
    libelles = [
        ("Revenus du mois", euros(kpi["revenus"])),
        ("Budget du mois", euros(kpi["budget_depenses"])),
        ("Dépenses du mois", euros(kpi["depenses"])),
        ("Reste disponible", euros(kpi["reste_disponible"])),
        ("Épargne nette", euros(kpi["epargne_nette"])),
        ("Taux d’épargne", f"{kpi['taux_epargne']:.1%}"),
    ]
    for colonne, (titre, valeur) in zip(colonnes, libelles):
        colonne.metric(titre, valeur)

    st.subheader("Analyse graphique")
    choix = st.selectbox(
        "Graphique",
        [
            "Évolution des dépenses cumulées du mois", "Dépenses par mois",
            "Équilibre mensuel", "Taux d’épargne par mois",
        ],
    )
    historique_brut = historique_mensuel(float(parametres.get("solde_initial_epargne", 0)))
    historique = pd.DataFrame(historique_brut)
    if not historique.empty:
        historique = historique[["mois", "depenses", "equilibre", "taux_epargne"]]
        historique.columns = ["Mois", "Dépenses", "Équilibre", "Taux d’épargne"]
        historique["Mois"] = historique["Mois"].map(libelle_mois)
    figure = _graphique_principal(choix, selection, historique)
    figure.update_layout(height=430, margin=dict(l=20, r=20, t=35, b=20))
    st.plotly_chart(figure, width="stretch")

    st.subheader("Budget prévu vs dépenses réelles par catégorie")
    comparaison = pd.DataFrame(comparaison_categories(selection))
    if comparaison.empty:
        st.info("Créez le budget du mois pour afficher cette comparaison.")
    else:
        comparaison = comparaison[["categorie", "budget_prevu", "reel"]]
        comparaison.columns = ["Catégorie", "Budget prévu", "Dépenses réelles"]
        long = comparaison.melt(id_vars="Catégorie", var_name="Série", value_name="Montant")
        graphique = px.bar(long, x="Catégorie", y="Montant", color="Série", barmode="group")
        st.plotly_chart(graphique, width="stretch")

    col_alertes, col_comparatif = st.columns(2, gap="large")
    with col_alertes:
        st.subheader("Alertes budget")
        alertes = alertes_budget(
            selection,
            float(parametres.get("seuil_vigilance_budget", 0.8)),
            float(parametres.get("seuil_alerte_budget", 1.0)),
        )
        if not alertes:
            st.success("Aucune alerte sur les catégories budgétées.")
        for alerte in alertes:
            st.warning(f"{alerte['categorie']} : {alerte['pourcentage_utilise']:.0%} — {alerte['statut']}")
    with col_comparatif:
        st.subheader("Comparatif M-1")
        comparatif = comparaison_mois_precedent(selection)
        st.metric(
            "Dépenses par rapport au mois précédent",
            euros(comparatif["depenses_courantes"]),
            delta=euros(-comparatif["variation"]),
            delta_color="normal",
        )
        st.caption(f"Mois précédent : {euros(comparatif['depenses_precedentes'])}")
