import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.services.epargne_service import tableau_epargne
from src.ui_styles import carte_kpi, couleurs_actives, styliser_graphique
from src.utils import euros, libelle_mois


def afficher(parametres: dict) -> None:
    couleurs = couleurs_actives(parametres)
    st.title("Épargne")
    solde_initial = float(parametres.get("solde_initial_epargne", 0))
    lignes = tableau_epargne(solde_initial)
    if not lignes:
        st.info("Ajoutez un budget ou une transaction pour commencer le suivi de l’épargne.")
        return

    mois = [ligne["mois"] for ligne in lignes]
    selection = st.selectbox(
        "Mois analysé", mois, index=len(mois) - 1, format_func=libelle_mois
    )
    ligne_selectionnee = next(ligne for ligne in lignes if ligne["mois"] == selection)
    cartes = st.columns(3, gap="large")
    carte_kpi(
        cartes[0], "Solde d’épargne", euros(ligne_selectionnee["solde_fin"]),
        couleurs["couleur_graphique_1"], f"À fin {libelle_mois(selection)}",
    )
    carte_kpi(
        cartes[1], "Épargne nette du mois", euros(ligne_selectionnee["epargne_reelle"]),
        couleurs["couleur_positive"] if ligne_selectionnee["epargne_reelle"] >= 0 else couleurs["couleur_negative"],
        f"Prévu : {euros(ligne_selectionnee['epargne_prevue'])}",
    )
    carte_kpi(
        cartes[2], "Taux d’épargne", f"{ligne_selectionnee['taux_epargne']:.1%}",
        couleurs["couleur_graphique_3"], "Épargne nette / revenus",
    )

    st.subheader("Évolution du solde d’épargne")
    graphique = go.Figure()
    graphique.add_trace(
        go.Scatter(
            x=[libelle_mois(ligne["mois"]) for ligne in lignes],
            y=[ligne["solde_fin"] for ligne in lignes],
            mode="lines+markers", name="Solde de fin",
            fill="tozeroy",
            line={"color": couleurs["couleur_graphique_1"], "width": 3},
            fillcolor=couleurs["couleur_bloc"],
            marker={"size": 7},
            hovertemplate="%{x}<br>Solde : %{y:,.2f} €<extra></extra>",
        )
    )
    graphique.update_yaxes(title="Solde")
    st.plotly_chart(
        styliser_graphique(graphique, couleurs, format_axe_y=",.0f €"),
        width="stretch",
    )

    st.subheader("Détail mensuel")
    dataframe = pd.DataFrame(lignes)
    dataframe["mois"] = dataframe["mois"].map(libelle_mois)
    dataframe["taux_epargne"] = dataframe["taux_epargne"] * 100
    dataframe.columns = [
        "Mois", "Revenus réels", "Épargne prévue", "Épargne réelle", "Écart",
        "Taux d’épargne", "Solde début", "Solde fin", "Statut",
    ]
    st.dataframe(
        dataframe, hide_index=True, width="stretch",
        column_config={
            "Revenus réels": st.column_config.NumberColumn(format="%.2f €"),
            "Épargne prévue": st.column_config.NumberColumn(format="%.2f €"),
            "Épargne réelle": st.column_config.NumberColumn(format="%.2f €"),
            "Écart": st.column_config.NumberColumn(format="%.2f €"),
            "Taux d’épargne": st.column_config.NumberColumn(format="%.1f %%"),
            "Solde début": st.column_config.NumberColumn(format="%.2f €"),
            "Solde fin": st.column_config.NumberColumn(format="%.2f €"),
        },
    )
    st.caption("Le solde de fin d’un mois devient automatiquement le solde de début du suivant.")
