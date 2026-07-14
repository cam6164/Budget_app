import pandas as pd
import streamlit as st

from src.config import TYPES_TRANSACTION
from src.services.categories_service import (
    ajouter_categorie,
    lister_categories,
    modifier_categorie,
    supprimer_categorie,
)


def afficher(_parametres: dict) -> None:
    st.title("Catégories")
    st.caption("Les catégories actives alimentent automatiquement les formulaires et les budgets.")
    categories = lister_categories()
    if categories:
        table = pd.DataFrame(categories)[["id", "type", "categorie", "actif", "ordre"]]
        table.columns = ["Identifiant", "Type", "Catégorie", "Active", "Ordre"]
        table["Active"] = table["Active"].astype(bool)
        st.dataframe(table, hide_index=True, width="stretch")

    col_ajout, col_modification = st.columns(2, gap="large")
    with col_ajout:
        st.subheader("Ajouter une catégorie")
        with st.form("ajout_categorie", clear_on_submit=True):
            type_categorie = st.selectbox("Type", TYPES_TRANSACTION)
            nom = st.text_input("Nom de la catégorie")
            active = st.checkbox("Catégorie active", value=True)
            if st.form_submit_button("Ajouter", type="primary", width="stretch"):
                try:
                    ajouter_categorie(type_categorie, nom, active)
                    st.success("Catégorie ajoutée. Les mois existants ont été complétés à 0 €.")
                    st.rerun()
                except Exception as erreur:
                    st.error(str(erreur))

    with col_modification:
        st.subheader("Modifier ou désactiver")
        if not categories:
            st.info("Aucune catégorie à modifier.")
            return
        index_par_libelle = {
            f"{c['type']} — {c['categorie']} (n°{c['id']})": c for c in categories
        }
        choix = st.selectbox("Catégorie", list(index_par_libelle), key="categorie_a_modifier")
        selection = index_par_libelle[choix]
        with st.form("modification_categorie"):
            nouveau_nom = st.text_input("Nouveau nom", value=selection["categorie"])
            active_modifiee = st.checkbox("Active", value=bool(selection["actif"]))
            ordre = st.number_input("Ordre", min_value=0, step=1, value=int(selection["ordre"] or 0))
            if st.form_submit_button("Enregistrer les modifications", width="stretch"):
                try:
                    modifier_categorie(selection["id"], nouveau_nom, active_modifiee, int(ordre))
                    st.success("Catégorie mise à jour.")
                    st.rerun()
                except Exception as erreur:
                    st.error(str(erreur))
        with st.expander("Suppression définitive"):
            st.warning("Une catégorie utilisée sera seulement désactivée.")
            confirmation = st.checkbox("Je confirme la demande de suppression", key="conf_sup_cat")
            if st.button("Supprimer cette catégorie", disabled=not confirmation):
                supprimee, message = supprimer_categorie(selection["id"])
                (st.success if supprimee else st.warning)(message)
                st.rerun()
