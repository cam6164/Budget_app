from datetime import date

import pandas as pd
import streamlit as st

from src.navigation import recharger_page
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


def _memoriser_mois_budget() -> None:
    st.session_state["dernier_mois_budget_selectionne"] = st.session_state.get(
        "mois_budget_selectionne"
    )


def _fermer_dialogue_suppression_budget() -> None:
    st.session_state["dialogue_suppression_budget_ouvert"] = False


@st.dialog(
    "Supprimer un mois de budget", on_dismiss=_fermer_dialogue_suppression_budget
)
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
    col_supprimer, col_annuler = st.columns(2)
    supprimer = col_supprimer.button(
        "Supprimer ce mois budget", type="primary", disabled=not confirmer,
        use_container_width=True,
    )
    if col_annuler.button("Annuler", use_container_width=True):
        _fermer_dialogue_suppression_budget()
        recharger_page("Budget mensuel")
    if supprimer:
        try:
            nombre = supprimer_mois_budget(mois)
            _fermer_dialogue_suppression_budget()
            st.session_state["message_budget"] = (
                f"Budget {libelle_mois(mois)} supprimé ({nombre} ligne(s)). "
                "Les transactions sont intactes."
            )
            mois_restants = [existant for existant in mois_existants if existant != mois]
            if mois_restants:
                st.session_state["mois_budget_selection_cible"] = mois_restants[-1]
            else:
                st.session_state["mois_budget_selection_cible"] = ""
            recharger_page("Budget mensuel")
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
        mois_options = {nom.capitalize(): numero for numero, nom in enumerate(MOIS_FR, 1)}
        mois_choisi = st.selectbox(
            "Mois de départ", list(mois_options), index=date.today().month - 1,
        )
        numero = mois_options[mois_choisi]
        st.caption("Vue annuelle simplifiée V1 : les 12 mois sont disponibles dans le sélecteur.")
        if st.button("Créer le premier budget", type="primary"):
            mois_cree = f"{int(annee):04d}-{int(numero):02d}"
            try:
                nombre = creer_budget_mensuel(mois_cree)
                st.session_state["mois_budget_selection_cible"] = mois_cree
                st.session_state["message_budget"] = (
                    f"Premier budget {libelle_mois(mois_cree)} créé "
                    f"avec {nombre} catégorie(s)."
                )
                recharger_page("Budget mensuel")
            except Exception as erreur:
                st.error(f"Création du premier budget impossible : {erreur}")
        return

    mois_cible = st.session_state.pop("mois_budget_selection_cible", None)
    if mois_cible in mois_existants:
        st.session_state["mois_budget_selectionne"] = mois_cible
        st.session_state["dernier_mois_budget_selectionne"] = mois_cible
    else:
        mois_memorise = st.session_state.get("dernier_mois_budget_selectionne")
        if mois_memorise in mois_existants:
            st.session_state["mois_budget_selectionne"] = mois_memorise
        elif st.session_state.get("mois_budget_selectionne") not in mois_existants:
            st.session_state["mois_budget_selectionne"] = mois_existants[-1]
            st.session_state["dernier_mois_budget_selectionne"] = mois_existants[-1]
    col_mois, col_action, col_suppression = st.columns([2, 1, 1])
    mois = col_mois.selectbox(
        "Mois", mois_existants, format_func=libelle_mois,
        key="mois_budget_selectionne",
        on_change=_memoriser_mois_budget,
    )
    if col_action.button("Créer le mois suivant", type="primary", width="stretch"):
        try:
            suivant = creer_mois_suivant()
            st.session_state["mois_budget_selection_cible"] = suivant
            st.session_state["message_budget"] = (
                f"Le budget {libelle_mois(suivant)} a été créé "
                "à partir du mois précédent."
            )
            recharger_page("Budget mensuel")
        except Exception as erreur:
            st.error(f"Création du mois suivant impossible : {erreur}")
    if col_suppression.button("Supprimer un mois budget", width="stretch"):
        st.session_state["dialogue_suppression_budget_ouvert"] = True
    if st.session_state.get("dialogue_suppression_budget_ouvert", False):
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
            recharger_page("Budget mensuel")
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
            key=(
                f"edition_budget_{mois}_"
                f"{st.session_state.get('version_edition_budget', 0)}"
            ),
        )
        col_enregistrer, col_annuler = st.columns(2)
        if col_enregistrer.button("Enregistrer les modifications", type="primary", width="stretch"):
            lignes = [
                {"id": int(ligne["Identifiant"]), "budget_prevu": float(ligne["Budget prévu"])}
                for _, ligne in modifie.iterrows()
            ]
            try:
                nombre = enregistrer_budgets(lignes)
                st.session_state["mode_modification_budget"] = False
                st.session_state["version_edition_budget"] = (
                    st.session_state.get("version_edition_budget", 0) + 1
                )
                st.session_state["mois_budget_selection_cible"] = mois
                st.session_state["message_budget"] = (
                    f"{nombre} budget(s) enregistré(s) pour {libelle_mois(mois)}. "
                    "Les indicateurs ont été recalculés."
                )
                recharger_page("Budget mensuel")
            except Exception as erreur:
                st.error(
                    "Enregistrement des budgets impossible : "
                    f"{type(erreur).__name__} — {erreur}"
                )
        if col_annuler.button("Annuler la modification", width="stretch"):
            st.session_state["mode_modification_budget"] = False
            st.session_state["version_edition_budget"] = (
                st.session_state.get("version_edition_budget", 0) + 1
            )
            st.session_state["mois_budget_selection_cible"] = mois
            recharger_page("Budget mensuel")
