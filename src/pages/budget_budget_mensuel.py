from datetime import date

import pandas as pd
import streamlit as st

from src.services.budget_service import (
    creer_budget_mensuel,
    creer_mois_suivant,
    enregistrer_budgets,
    mois_budget_disponibles,
    rapport_budget,
)
from src.utils import MOIS_FR, libelle_mois


def afficher(parametres: dict) -> None:
    st.title("Budget mensuel")
    mois_existants = mois_budget_disponibles()
    if not mois_existants:
        st.subheader("Créer votre premier budget")
        st.write("Choisissez une année puis le premier mois à préparer.")
        annee = st.number_input(
            "Année", min_value=2000, max_value=2100, value=date.today().year, step=1
        )
        numero = st.selectbox(
            "Mois de départ", range(1, 13), index=date.today().month - 1,
            format_func=lambda n: f"{MOIS_FR[n - 1]}-{int(annee) % 100:02d}",
        )
        st.caption("Vue annuelle simplifiée V1 : les 12 mois sont disponibles dans le sélecteur.")
        if st.button("Créer le premier budget", type="primary"):
            nombre = creer_budget_mensuel(f"{int(annee):04d}-{int(numero):02d}")
            st.success(f"Premier budget créé avec {nombre} catégories.")
            st.rerun()
        return

    col_mois, col_action = st.columns([2, 1])
    mois = col_mois.selectbox(
        "Mois", mois_existants, index=len(mois_existants) - 1, format_func=libelle_mois
    )
    if col_action.button("Créer le mois suivant", width="stretch"):
        suivant = creer_mois_suivant()
        st.success(f"Le budget {libelle_mois(suivant)} a été créé à partir du mois précédent.")
        st.rerun()

    rapport = rapport_budget(
        mois,
        float(parametres.get("seuil_vigilance_budget", 0.8)),
        float(parametres.get("seuil_alerte_budget", 1.0)),
    )
    if not rapport:
        st.info("Aucune ligne de budget pour ce mois.")
        return
    edition = pd.DataFrame(rapport)
    edition_affichee = edition[[
        "id", "mois", "type", "categorie", "budget_prevu", "reel",
        "ecart", "pourcentage_utilise", "statut",
    ]].copy()
    edition_affichee["mois"] = edition_affichee["mois"].map(libelle_mois)
    edition_affichee.columns = [
        "Identifiant", "Mois", "Type", "Catégorie", "Budget prévu", "Réel",
        "Écart", "% utilisé", "Statut",
    ]
    modifie = st.data_editor(
        edition_affichee,
        hide_index=True,
        width="stretch",
        disabled=["Identifiant", "Mois", "Type", "Catégorie", "Réel", "Écart", "% utilisé", "Statut"],
        column_config={
            "Identifiant": None,
            "Budget prévu": st.column_config.NumberColumn(min_value=0.0, step=10.0, format="%.2f €"),
            "Réel": st.column_config.NumberColumn(format="%.2f €"),
            "Écart": st.column_config.NumberColumn(format="%.2f €"),
            "% utilisé": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.0f %%"),
        },
        key=f"edition_budget_{mois}",
    )
    if st.button("Enregistrer les budgets prévus", type="primary"):
        lignes = [
            {"id": int(ligne["Identifiant"]), "budget_prevu": float(ligne["Budget prévu"])}
            for _, ligne in modifie.iterrows()
        ]
        enregistrer_budgets(lignes)
        st.success("Budgets enregistrés et indicateurs recalculés.")
        st.rerun()
