import streamlit as st

from src.database import initialiser_base, lire_parametres
from src.navigation import afficher_navigation
from src.pages import (
    accueil,
    budget_budget_mensuel,
    budget_categories,
    budget_epargne,
    budget_import_bancaire,
    budget_parametres,
    budget_tableau_de_bord,
    budget_transactions,
)
from src.themes import appliquer_theme
from src.ui_styles import appliquer_configuration_affichage


st.set_page_config(
    page_title="Suivi budget et finances",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "sidebar_open" not in st.session_state:
    st.session_state["sidebar_open"] = True


def main() -> None:
    try:
        initialiser_base()
        parametres = lire_parametres()
    except Exception as erreur:
        st.error(f"Impossible d’initialiser la base locale : {erreur}")
        st.stop()

    appliquer_theme(parametres.get("theme_actif", "Sombre bleu"))
    appliquer_configuration_affichage(parametres)
    page = afficher_navigation()
    routes = {
        "Accueil": accueil.afficher,
        "Tableau de bord": budget_tableau_de_bord.afficher,
        "Transactions": budget_transactions.afficher,
        "Import bancaire": budget_import_bancaire.afficher,
        "Budget mensuel": budget_budget_mensuel.afficher,
        "Épargne": budget_epargne.afficher,
        "Catégories": budget_categories.afficher,
        "Paramètres": budget_parametres.afficher,
    }
    routes[page](parametres)


if __name__ == "__main__":
    main()
