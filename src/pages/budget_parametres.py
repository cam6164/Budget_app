import streamlit as st

from src.database import enregistrer_parametres
from src.services.backup_service import (
    creer_sauvegarde,
    exporter_transactions_csv,
    lister_sauvegardes,
    restaurer_sauvegarde,
)
from src.themes import THEMES


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
