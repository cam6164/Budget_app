import pandas as pd
import streamlit as st

from src.config import MOYENS_PAIEMENT, SENS_REMBOURSEMENT, STATUTS_IMPORT, TYPES_TRANSACTION
from src.services.categories_service import noms_categories
from src.services.import_bancaire_service import (
    ErreurValidationImport,
    detecter_colonnes,
    detecter_doublons_import,
    est_ligne_selectionnee,
    lire_fichier_bancaire,
    preparer_transactions_import,
    valider_import,
)
from src.ui_styles import hauteur_apercu, hauteur_tableau
from src.utils import ajouter_mois, libelle_mois

try:
    from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

    AGGRID_DISPONIBLE = True
except ImportError:
    AGGRID_DISPONIBLE = False


INTERNE_VERS_AFFICHAGE = {
    "importer": "Importer",
    "date_reelle": "Date réelle",
    "mois_reel": "Mois réel",
    "mois_budget": "Mois budget",
    "type": "Type",
    "sens_remboursement": "Sens remboursement",
    "categorie": "Catégorie",
    "categorie_remboursee": "Catégorie remboursée",
    "libelle": "Libellé",
    "libelle_bancaire_brut": "Libellé bancaire brut",
    "montant_bancaire": "Montant bancaire",
    "montant_budget": "Montant budget",
    "moyen_paiement": "Moyen de paiement",
    "commentaire": "Commentaire",
    "statut_import": "Statut import",
}
AFFICHAGE_VERS_INTERNE = {valeur: cle for cle, valeur in INTERNE_VERS_AFFICHAGE.items()}


def _index_suggestion(options: list[str], suggestion: str | None) -> int:
    return options.index(suggestion) if suggestion in options else 0


def _mois_relecture(dataframe: pd.DataFrame) -> list[str]:
    mois: set[str] = set()
    for valeur in dataframe["mois_reel"].dropna().astype(str):
        for decalage in range(-2, 3):
            mois.add(ajouter_mois(valeur, decalage))
    mois.update(dataframe["mois_budget"].dropna().astype(str))
    return [libelle_mois(valeur) for valeur in sorted(mois)]


def _vers_affichage(dataframe: pd.DataFrame) -> pd.DataFrame:
    affichage = dataframe.rename(columns=INTERNE_VERS_AFFICHAGE).copy()
    for colonne in ("Mois réel", "Mois budget"):
        affichage[colonne] = affichage[colonne].map(
            lambda valeur: libelle_mois(str(valeur)) if valeur else ""
        )
    return affichage


def _vers_interne(dataframe: pd.DataFrame) -> pd.DataFrame:
    interne = dataframe.rename(columns=AFFICHAGE_VERS_INTERNE).copy()
    for colonne in INTERNE_VERS_AFFICHAGE:
        if colonne not in interne:
            interne[colonne] = ""
    return interne[list(INTERNE_VERS_AFFICHAGE)]


def _editeur_natif(
    affichage: pd.DataFrame,
    categories: list[str],
    categories_depense: list[str],
    mois: list[str],
    hauteur: int,
) -> pd.DataFrame:
    return st.data_editor(
        affichage,
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        height=hauteur,
        disabled=["Libellé bancaire brut"],
        column_config={
            "Importer": st.column_config.CheckboxColumn(),
            "Type": st.column_config.SelectboxColumn(options=TYPES_TRANSACTION),
            "Sens remboursement": st.column_config.SelectboxColumn(options=[""] + SENS_REMBOURSEMENT),
            "Catégorie": st.column_config.SelectboxColumn(options=[""] + categories),
            "Catégorie remboursée": st.column_config.SelectboxColumn(options=[""] + categories_depense),
            "Moyen de paiement": st.column_config.SelectboxColumn(options=MOYENS_PAIEMENT),
            "Statut import": st.column_config.SelectboxColumn(options=STATUTS_IMPORT),
            "Mois réel": st.column_config.SelectboxColumn(options=mois),
            "Mois budget": st.column_config.SelectboxColumn(options=mois),
            "Montant bancaire": st.column_config.NumberColumn(format="%.2f €"),
            "Montant budget": st.column_config.NumberColumn(format="%.2f €"),
        },
        key="table_import_native",
    )


def _editeur_aggrid(
    affichage: pd.DataFrame,
    categories: list[str],
    categories_depense: list[str],
    mois: list[str],
    hauteur: int,
) -> pd.DataFrame:
    constructeur = GridOptionsBuilder.from_dataframe(affichage)
    constructeur.configure_default_column(editable=True, resizable=True, minWidth=125)
    constructeur.configure_column(
        "Importer", editable=True,
        cellEditor="agCheckboxCellEditor", cellRenderer="agCheckboxCellRenderer",
    )
    constructeur.configure_column("Libellé bancaire brut", editable=False)
    listes = {
        "Type": TYPES_TRANSACTION,
        "Sens remboursement": [""] + SENS_REMBOURSEMENT,
        "Catégorie": [""] + categories,
        "Catégorie remboursée": [""] + categories_depense,
        "Moyen de paiement": MOYENS_PAIEMENT,
        "Statut import": STATUTS_IMPORT,
        # Limite V1.5 : la liste réunit M-2 à M+2 de toutes les lignes du fichier.
        # Elle reste lisible en français sans calendrier annuel dans chaque cellule.
        "Mois réel": mois,
        "Mois budget": mois,
    }
    for colonne, valeurs in listes.items():
        constructeur.configure_column(
            colonne,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": valeurs},
        )
    reponse = AgGrid(
        affichage,
        gridOptions=constructeur.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=False,
        height=hauteur,
        theme="streamlit",
        key="table_import_aggrid",
    )
    return pd.DataFrame(reponse["data"])


def afficher(parametres: dict) -> None:
    st.title("Import bancaire")
    st.caption("Import manuel de fichiers CSV ou Excel .xlsx — aucune connexion bancaire.")
    if message := st.session_state.pop("message_import_bancaire", None):
        st.success(message)

    fichier = st.file_uploader(
        "Sélectionner un relevé bancaire", type=["csv", "xlsx"],
        help="Formats pris en charge : CSV séparé par point-virgule, virgule ou tabulation, et Excel .xlsx.",
    )
    if fichier is not None:
        try:
            brut = lire_fichier_bancaire(fichier)
        except Exception as erreur:
            st.error(str(erreur))
            return
        st.subheader("Aperçu du fichier")
        st.write(f"{len(brut)} ligne(s), {len(brut.columns)} colonne(s) détectée(s).")
        st.dataframe(
            brut.head(20), hide_index=True, width="stretch",
            height=hauteur_apercu(parametres),
        )

        suggestions = detecter_colonnes(brut)
        colonnes = list(brut.columns)
        options_facultatives = ["— Non utilisée —"] + colonnes
        st.subheader("Association des colonnes")
        col_date, col_libelle = st.columns(2)
        colonne_date = col_date.selectbox(
            "Date réelle", colonnes,
            index=_index_suggestion(colonnes, suggestions.get("date_reelle")),
        )
        colonne_libelle = col_libelle.selectbox(
            "Libellé", colonnes,
            index=_index_suggestion(colonnes, suggestions.get("libelle")),
        )
        mode_montant = st.radio(
            "Organisation des montants",
            ["Une colonne Montant", "Deux colonnes Débit et Crédit"],
            horizontal=True,
        )
        mapping = {"date_reelle": colonne_date, "libelle": colonne_libelle}
        if mode_montant == "Une colonne Montant":
            choix_montant = st.selectbox(
                "Montant", options_facultatives,
                index=_index_suggestion(options_facultatives, suggestions.get("montant")),
            )
            if choix_montant != "— Non utilisée —":
                mapping["montant"] = choix_montant
        else:
            col_debit, col_credit = st.columns(2)
            choix_debit = col_debit.selectbox(
                "Débit", options_facultatives,
                index=_index_suggestion(options_facultatives, suggestions.get("debit")),
            )
            choix_credit = col_credit.selectbox(
                "Crédit", options_facultatives,
                index=_index_suggestion(options_facultatives, suggestions.get("credit")),
            )
            if choix_debit != "— Non utilisée —":
                mapping["debit"] = choix_debit
            if choix_credit != "— Non utilisée —":
                mapping["credit"] = choix_credit

        if st.button("Préparer les transactions", type="primary"):
            try:
                preparees = preparer_transactions_import(brut, mapping)
                erreurs = preparees.attrs.get("erreurs_lecture", [])
                st.session_state["transactions_import_preparees"] = detecter_doublons_import(preparees)
                if erreurs:
                    detail_erreurs = " ; ".join(erreurs[:3])
                    st.warning(
                        f"{len(erreurs)} ligne(s) non exploitable(s) ont été écartées. "
                        f"{detail_erreurs}"
                    )
            except Exception as erreur:
                st.error(str(erreur))

    preparees = st.session_state.get("transactions_import_preparees")
    if preparees is None or preparees.empty:
        return
    st.divider()
    st.subheader("Relecture et modification")
    st.info(
        "Vérifiez les affectations, complétez notamment les lignes WERO, "
        "puis cochez uniquement les lignes à importer."
    )
    categories = sorted(
        {categorie for type_categorie in TYPES_TRANSACTION for categorie in noms_categories(type_categorie, True)}
    )
    categories_depense = noms_categories("Dépense", True)
    mois = _mois_relecture(preparees)
    affichage = _vers_affichage(preparees)
    hauteur_grille = hauteur_tableau(parametres, grille=True)
    if AGGRID_DISPONIBLE:
        editee = _editeur_aggrid(
            affichage, categories, categories_depense, mois, hauteur_grille
        )
    else:
        st.caption("Éditeur Streamlit actif ; l’éditeur avancé sera disponible après installation des dépendances.")
        editee = _editeur_natif(
            affichage, categories, categories_depense, mois, hauteur_grille
        )
    interne = _vers_interne(editee)
    nombre_selectionne = sum(
        est_ligne_selectionnee(valeur) for valeur in interne["importer"]
    )
    st.write(f"{nombre_selectionne} ligne(s) sélectionnée(s) pour l’import.")
    col_valider, col_annuler = st.columns(2)
    if col_valider.button("Valider l’import", type="primary", width="stretch"):
        try:
            nombre = valider_import(interne)
            st.session_state.pop("transactions_import_preparees", None)
            if nombre:
                st.session_state["message_import_bancaire"] = (
                    f"Import terminé : {nombre} transaction(s) ajoutée(s). Une sauvegarde a été créée."
                )
            else:
                st.session_state["message_import_bancaire"] = (
                    "Aucune transaction n’a été importée : aucune ligne sélectionnée et validable."
                )
            st.rerun()
        except ErreurValidationImport as erreur:
            st.error(
                f"Validation interrompue à l’étape « {erreur.etape} » : "
                f"{erreur.message_detail}"
            )
        except Exception as erreur:
            st.error(
                "Validation interrompue à une étape inattendue : "
                f"{type(erreur).__name__} — {erreur}"
            )
    if col_annuler.button("Annuler la préparation", width="stretch"):
        st.session_state.pop("transactions_import_preparees", None)
        st.rerun()
