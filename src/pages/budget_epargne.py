import pandas as pd
import streamlit as st

from src.services.epargne_service import tableau_epargne
from src.ui_styles import hauteur_tableau
from src.utils import libelle_mois


def afficher(parametres: dict) -> None:
    st.title("Épargne")
    lignes = tableau_epargne(float(parametres.get("solde_initial_epargne", 0)))
    if not lignes:
        st.info("Ajoutez un budget ou une transaction pour commencer le suivi de l’épargne.")
        return

    dataframe = pd.DataFrame(lignes)
    dataframe["mois"] = dataframe["mois"].map(libelle_mois)
    dataframe["taux_epargne"] = dataframe["taux_epargne"] * 100
    dataframe.columns = [
        "Mois", "Revenus réels", "Épargne prévue", "Épargne réelle", "Écart",
        "Taux d’épargne", "Solde début", "Solde fin", "Statut",
    ]
    st.dataframe(
        dataframe,
        hide_index=True,
        width="stretch",
        height=hauteur_tableau(parametres),
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
    st.caption(
        "Le solde de fin d’un mois devient automatiquement le solde de début du suivant."
    )
