from datetime import date

import pandas as pd
import streamlit as st

from src.services.budget_service import (
    creer_budget_mensuel,
    creer_mois_suivant,
    enregistrer_budgets,
    mois_budget_disponibles,
    rapport_budget,
    supprimer_mois_budget,
)
from src.ui_styles import couleurs_actives, hauteur_tableau
from src.utils import MOIS_FR, libelle_mois


@st.dialog("Supprimer un mois de budget")
def _dialog_suppression_mois(mois_existants: list[str], mois_courant: str) -> None:
    mois = st.selectbox(
        "Mois à supprimer",
        mois_existants,
        index=mois_existants.index(mois_courant),
        format_func=libelle_mois,
    )
    st.warning(
        "Seules les lignes de budget de ce mois seront supprimées. "
        "Les transactions seront conservées."
    )
    confirmer = st.checkbox(
        f"Je confirme la suppression du budget {libelle_mois(mois)}"
    )
    if st.button(
        "Supprimer ce mois budget", type="primary", disabled=not confirmer,
        use_container_width=True,
    ):
        try:
            nombre = supprimer_mois_budget(mois)
            st.session_state["message_budget"] = (
                f"Budget {libelle_mois(mois)} supprimé ({nombre} ligne(s)). "
                "Les transactions sont intactes."
            )
            st.rerun()
        except Exception as erreur:
            st.error(f"Suppression du budget impossible : {erreur}")


def afficher(parametres: dict) -> None:
    couleurs = couleurs_actives(parametres)
    table_height = hauteur_tableau(parametres)
    st.title("Budget mensuel")
    if message := st.session_state.pop("message_budget", None):
        st.success(message)
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

    col_mois, col_action, col_suppression = st.columns([2, 1, 1])
    mois = col_mois.selectbox(
        "Mois", mois_existants, index=len(mois_existants) - 1, format_func=libelle_mois
    )
    if col_action.button("Créer le mois suivant", type="primary", width="stretch"):
        suivant = creer_mois_suivant()
        st.success(f"Le budget {libelle_mois(suivant)} a été créé à partir du mois précédent.")
        st.rerun()
    if col_suppression.button("Supprimer un mois budget", width="stretch"):
        _dialog_suppression_mois(mois_existants, mois)
    st.caption(f"Budget affiché : {libelle_mois(mois)}")

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
    mode_modification = st.session_state.get("mode_modification_budget", False)
    if not mode_modification:
        vue = edition_affichee.drop(columns=["Identifiant"]).copy()
        vue["Statut"] = vue["Statut"].map(
            {"OK": "● OK", "Vigilance": "● Vigilance", "Dépassement": "● Dépassement"}
        ).fillna(vue["Statut"])

        def style_statut(valeur: str) -> str:
            if "Dépassement" in valeur:
                return f"color:{couleurs['couleur_negative']};font-weight:700"
            if "Vigilance" in valeur:
                return f"color:{couleurs['couleur_vigilance']};font-weight:700"
            return f"color:{couleurs['couleur_positive']};font-weight:700"

        style = vue.style.map(style_statut, subset=["Statut"])
        st.dataframe(
            style,
            hide_index=True,
            width="stretch",
            height=table_height,
            column_config={
                "Budget prévu": st.column_config.NumberColumn(format="%.2f €"),
                "Réel": st.column_config.NumberColumn(format="%.2f €"),
                "Écart": st.column_config.NumberColumn(format="%.2f €"),
                "% utilisé": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.0f %%"),
            },
        )
        if st.button("Modifier les budgets", type="primary"):
            st.session_state["mode_modification_budget"] = True
            st.rerun()
    else:
        st.info("Mode modification actif : seule la colonne Budget prévu est modifiable.")
        modifie = st.data_editor(
            edition_affichee,
            hide_index=True,
            width="stretch",
            height=table_height,
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
        col_enregistrer, col_annuler = st.columns(2)
        if col_enregistrer.button("Enregistrer les budgets prévus", type="primary", width="stretch"):
            lignes = [
                {"id": int(ligne["Identifiant"]), "budget_prevu": float(ligne["Budget prévu"])}
                for _, ligne in modifie.iterrows()
            ]
            enregistrer_budgets(lignes)
            st.session_state["mode_modification_budget"] = False
            st.success("Budgets enregistrés et indicateurs recalculés.")
            st.rerun()
        if col_annuler.button("Annuler la modification", width="stretch"):
            st.session_state["mode_modification_budget"] = False
            st.rerun()
