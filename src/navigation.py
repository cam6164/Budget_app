import streamlit as st


PAGES = [
    "Accueil", "Tableau de bord", "Transactions", "Import bancaire", "Budget mensuel",
    "Épargne", "Catégories", "Paramètres",
]


def afficher_navigation() -> str:
    cible = st.session_state.pop("navigation_cible", None)
    if cible in PAGES:
        st.session_state["page_active"] = cible
    with st.sidebar:
        st.title("Budget personnel")
        st.caption("Suivi budget et finances")
        page = st.radio("Navigation", PAGES, key="page_active", label_visibility="collapsed")
        st.divider()
        st.caption("Données conservées uniquement sur cet ordinateur")
    return page
