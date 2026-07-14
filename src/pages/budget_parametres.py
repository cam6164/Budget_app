import pandas as pd
import streamlit as st

from src.config import SENS_REMBOURSEMENT, TYPES_TRANSACTION
from src.database import enregistrer_parametres
from src.services.backup_service import (
    creer_sauvegarde,
    exporter_transactions_csv,
    lister_sauvegardes,
    restaurer_sauvegarde,
)
from src.services.categories_service import noms_categories
from src.services.regles_affectation_service import (
    ajouter_regle,
    lister_regles,
    modifier_regle,
    supprimer_regle,
)
from src.themes import THEMES


def _index_option(options: list[str], valeur: str | None) -> int:
    return options.index(valeur) if valeur in options else 0


def _afficher_regles_affectation() -> None:
    st.divider()
    st.subheader("Règles d’affectation bancaire")
    st.caption("La priorité numérique la plus faible est appliquée en premier.")
    regles = lister_regles()
    if regles:
        table = pd.DataFrame(regles)[[
            "id", "mot_cle", "type_attribue", "categorie_attribuee",
            "sens_remboursement", "categorie_remboursee", "actif", "priorite",
        ]]
        table.columns = [
            "Identifiant", "Mot-clé", "Type attribué", "Catégorie attribuée",
            "Sens remboursement", "Catégorie remboursée", "Actif", "Priorité",
        ]
        table["Actif"] = table["Actif"].astype(bool)
        st.dataframe(table, hide_index=True, width="stretch")

    categories = sorted(
        {categorie for type_categorie in TYPES_TRANSACTION for categorie in noms_categories(type_categorie, True)}
    )
    categories_options = [""] + categories
    categories_depense = [""] + noms_categories("Dépense", True)
    sens_options = [""] + SENS_REMBOURSEMENT

    with st.expander("Ajouter une règle"):
        with st.form("ajouter_regle_affectation", clear_on_submit=True):
            mot_cle = st.text_input("Mot-clé")
            type_attribue = st.selectbox("Type attribué", TYPES_TRANSACTION)
            categorie = st.selectbox("Catégorie attribuée", categories_options)
            sens = st.selectbox("Sens remboursement", sens_options)
            categorie_remboursee = st.selectbox("Catégorie remboursée", categories_depense)
            actif = st.checkbox("Actif", value=True)
            priorite = st.number_input("Priorité", min_value=0, value=100, step=1)
            if st.form_submit_button("Ajouter la règle", type="primary"):
                try:
                    ajouter_regle(
                        mot_cle, type_attribue, categorie, sens,
                        categorie_remboursee, actif, int(priorite),
                    )
                    st.success("Règle ajoutée.")
                    st.rerun()
                except Exception as erreur:
                    st.error(str(erreur))

    if not regles:
        return
    libelles = {
        f"n°{regle['id']} — {regle['mot_cle']} — priorité {regle['priorite']}": regle
        for regle in regles
    }
    choix = st.selectbox("Règle à modifier", list(libelles), key="regle_a_modifier")
    selection = libelles[choix]
    categories_selection = categories_options.copy()
    if selection["categorie_attribuee"] not in categories_selection:
        categories_selection.append(selection["categorie_attribuee"])
    categories_remboursement_selection = categories_depense.copy()
    if selection["categorie_remboursee"] not in categories_remboursement_selection:
        categories_remboursement_selection.append(selection["categorie_remboursee"])
    with st.form("modifier_regle_affectation"):
        mot_modifie = st.text_input("Mot-clé", value=selection["mot_cle"])
        type_modifie = st.selectbox(
            "Type attribué", TYPES_TRANSACTION,
            index=_index_option(TYPES_TRANSACTION, selection["type_attribue"]),
            key="type_regle_modifie",
        )
        categorie_modifiee = st.selectbox(
            "Catégorie attribuée", categories_selection,
            index=_index_option(categories_selection, selection["categorie_attribuee"]),
            key="categorie_regle_modifiee",
        )
        sens_modifie = st.selectbox(
            "Sens remboursement", sens_options,
            index=_index_option(sens_options, selection["sens_remboursement"]),
            key="sens_regle_modifie",
        )
        categorie_remboursee_modifiee = st.selectbox(
            "Catégorie remboursée", categories_remboursement_selection,
            index=_index_option(categories_remboursement_selection, selection["categorie_remboursee"]),
            key="categorie_remboursee_regle_modifiee",
        )
        actif_modifie = st.checkbox("Actif", value=bool(selection["actif"]), key="actif_regle_modifie")
        priorite_modifiee = st.number_input(
            "Priorité", min_value=0, value=int(selection["priorite"]), step=1,
            key="priorite_regle_modifiee",
        )
        if st.form_submit_button("Enregistrer la règle"):
            try:
                modifier_regle(
                    selection["id"], mot_modifie, type_modifie,
                    categorie_modifiee, sens_modifie,
                    categorie_remboursee_modifiee, actif_modifie,
                    int(priorite_modifiee),
                )
                st.success("Règle mise à jour.")
                st.rerun()
            except Exception as erreur:
                st.error(str(erreur))
    confirmer_suppression = st.checkbox(
        "Je confirme la suppression de cette règle", key="confirmer_suppression_regle"
    )
    if st.button("Supprimer la règle", disabled=not confirmer_suppression):
        supprimer_regle(selection["id"])
        st.success("Règle supprimée.")
        st.rerun()


def afficher(parametres: dict) -> None:
    st.title("Paramètres")
    st.subheader("Préférences")
    noms_themes = list(THEMES)
    theme_actuel = parametres.get("theme_actif", "Vert pastel")
    with st.form("parametres_generaux"):
        theme = st.selectbox(
            "Thème actif", noms_themes,
            index=noms_themes.index(theme_actuel) if theme_actuel in noms_themes else 0,
        )
        solde = st.number_input(
            "Solde initial d’épargne", value=float(parametres.get("solde_initial_epargne", 0)),
            step=100.0, format="%.2f",
        )
        vigilance = st.number_input(
            "Seuil vigilance budget (%)", min_value=0.0, max_value=1000.0,
            value=float(parametres.get("seuil_vigilance_budget", 0.8)) * 100, step=5.0,
        )
        alerte = st.number_input(
            "Seuil alerte budget (%)", min_value=0.0, max_value=1000.0,
            value=float(parametres.get("seuil_alerte_budget", 1.0)) * 100, step=5.0,
        )
        if st.form_submit_button("Enregistrer les paramètres", type="primary"):
            if alerte < vigilance:
                st.error("Le seuil d’alerte doit être supérieur ou égal au seuil de vigilance.")
            else:
                enregistrer_parametres({
                    "theme_actif": theme,
                    "solde_initial_epargne": solde,
                    "seuil_vigilance_budget": vigilance / 100,
                    "seuil_alerte_budget": alerte / 100,
                })
                st.success("Paramètres enregistrés.")
                st.rerun()

    _afficher_regles_affectation()
    st.divider()
    st.subheader("Sauvegarde et export")
    c1, c2 = st.columns(2)
    if c1.button("Créer une sauvegarde manuelle", width="stretch"):
        try:
            chemin = creer_sauvegarde()
            st.success(f"Sauvegarde créée : {chemin.name}")
        except Exception as erreur:
            st.error(str(erreur))
    if c2.button("Exporter les transactions en CSV", width="stretch"):
        try:
            chemin = exporter_transactions_csv()
            st.success(f"Export créé dans exports : {chemin.name}")
        except Exception as erreur:
            st.error(f"Export impossible : {erreur}")

    sauvegardes = lister_sauvegardes()
    st.subheader("Restaurer une sauvegarde")
    if not sauvegardes:
        st.info("Aucune sauvegarde disponible.")
    else:
        choix = st.selectbox("Fichier de sauvegarde", [fichier.name for fichier in sauvegardes])
        confirmation = st.checkbox(
            "Je confirme la restauration (une sauvegarde de sécurité sera créée avant l’opération)"
        )
        if st.button("Restaurer", disabled=not confirmation):
            try:
                restaurer_sauvegarde(choix)
                st.success("Sauvegarde restaurée. L’application va recharger les données.")
                st.rerun()
            except Exception as erreur:
                st.error(f"Restauration impossible : {erreur}")
