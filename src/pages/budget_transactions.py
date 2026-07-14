from datetime import date

import pandas as pd
import streamlit as st

from src.config import MOYENS_PAIEMENT, SENS_REMBOURSEMENT, TYPES_TRANSACTION
from src.services.budget_service import mois_budget_disponibles
from src.services.categories_service import noms_categories
from src.services.transactions_service import (
    ajouter_transaction,
    lister_transactions,
    mois_disponibles,
    supprimer_transaction,
)
from src.utils import MOIS_FR, choix_mois_autour, euros, libelle_mois, mois_canonique


def _mois_manuel(date_transaction: date, mode: str, annee: int, numero_mois: int) -> str | None:
    if mode == "Automatique":
        return None
    reference = mois_canonique(date_transaction)
    if mode == "Autre":
        return f"{annee:04d}-{numero_mois:02d}"
    return choix_mois_autour(reference)[mode]


def afficher(_parametres: dict) -> None:
    st.title("Transactions")
    tous_mois = sorted(set(mois_disponibles()) | set(mois_budget_disponibles()))
    toutes_categories = sorted({c for t in TYPES_TRANSACTION for c in noms_categories(t, False)})
    c1, c2, c3, c4 = st.columns(4)
    filtre_mois = c1.selectbox("Mois budget", ["Tous"] + tous_mois, format_func=lambda x: x if x == "Tous" else libelle_mois(x))
    filtre_type = c2.selectbox("Type", ["Tous"] + TYPES_TRANSACTION)
    filtre_categorie = c3.selectbox("Catégorie", ["Toutes"] + toutes_categories)
    recherche = c4.text_input("Rechercher un libellé")
    transactions = lister_transactions(
        None if filtre_mois == "Tous" else filtre_mois,
        None if filtre_type == "Tous" else filtre_type,
        None if filtre_categorie == "Toutes" else filtre_categorie,
        recherche or None,
    )
    if transactions:
        df = pd.DataFrame(transactions)
        affichage = df[[
            "id", "date_reelle", "mois_budget", "type", "categorie",
            "categorie_remboursee", "libelle", "montant_bancaire", "montant_budget",
            "moyen_paiement", "commentaire",
        ]].copy()
        affichage["mois_budget"] = affichage["mois_budget"].map(libelle_mois)
        affichage.columns = [
            "Identifiant", "Date réelle", "Mois budget", "Type", "Catégorie",
            "Catégorie remboursée", "Libellé", "Montant bancaire", "Montant budget",
            "Moyen de paiement", "Commentaire",
        ]
        st.dataframe(
            affichage, hide_index=True, width="stretch",
            column_config={
                "Montant bancaire": st.column_config.NumberColumn(format="%.2f €"),
                "Montant budget": st.column_config.NumberColumn(format="%.2f €"),
            },
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Transactions sélectionnées", len(df))
        m2.metric("Total bancaire", euros(float(df["montant_bancaire"].sum())))
        m3.metric("Total budget", euros(float(df["montant_budget"].sum())))
    else:
        st.info("Aucune transaction ne correspond à la sélection.")

    if st.button("Ajouter une transaction", type="primary"):
        st.session_state["afficher_ajout_transaction"] = True
    if st.session_state.get("afficher_ajout_transaction", False):
        st.subheader("Ajouter une transaction")
        type_transaction = st.selectbox("Type", TYPES_TRANSACTION, key="type_nouvelle_transaction")
        categories = noms_categories(type_transaction, True)
        categories_depense = noms_categories("Dépense", True)
        if not categories:
            st.warning("Aucune catégorie active pour ce type. Ajoutez-en une dans Catégories.")
        with st.form("ajout_transaction", clear_on_submit=False):
            date_reelle = st.date_input("Date réelle", value=date.today())
            sens = st.selectbox("Sens remboursement", SENS_REMBOURSEMENT) if type_transaction == "Remboursement" else None
            categorie = st.selectbox("Catégorie", categories) if categories else None
            categorie_remboursee = st.selectbox("Catégorie remboursée", categories_depense) if type_transaction == "Remboursement" else None
            libelle = st.text_input("Libellé")
            montant = st.number_input("Montant", min_value=0.0, step=1.0, format="%.2f")
            moyen = st.selectbox("Moyen de paiement", MOYENS_PAIEMENT)
            mode_mois = st.selectbox("Mois budget", ["Automatique", "M-2", "M-1", "M", "M+1", "M+2", "Autre"])
            col_annee, col_mois = st.columns(2)
            annee = col_annee.number_input("Année (pour Autre)", min_value=2000, max_value=2100, value=date_reelle.year, step=1)
            numero_mois = col_mois.selectbox("Mois (pour Autre)", range(1, 13), index=date_reelle.month - 1, format_func=lambda n: MOIS_FR[n - 1])
            commentaire = st.text_area("Commentaire")
            col_valider, col_annuler = st.columns(2)
            valider = col_valider.form_submit_button("Enregistrer", type="primary", width="stretch", disabled=not categories)
            annuler = col_annuler.form_submit_button("Annuler", width="stretch")
            if annuler:
                st.session_state["afficher_ajout_transaction"] = False
                st.rerun()
            if valider:
                try:
                    ajouter_transaction(
                        date_reelle, type_transaction, categorie, libelle, montant, moyen,
                        _mois_manuel(date_reelle, mode_mois, int(annee), int(numero_mois)),
                        commentaire, sens, categorie_remboursee,
                    )
                    st.session_state["afficher_ajout_transaction"] = False
                    st.success("Transaction ajoutée.")
                    st.rerun()
                except Exception as erreur:
                    st.error(str(erreur))

    if transactions:
        with st.expander("Supprimer une transaction"):
            libelles = {f"n°{t['id']} — {t['date_reelle']} — {t['libelle']}": t["id"] for t in transactions}
            choix = st.selectbox("Transaction à supprimer", list(libelles))
            confirmer = st.checkbox("Je confirme la suppression définitive")
            if st.button("Supprimer", disabled=not confirmer):
                supprimer_transaction(libelles[choix])
                st.success("Transaction supprimée.")
                st.rerun()
