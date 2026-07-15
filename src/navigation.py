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
        page_active = st.session_state.get("page_active", "Accueil")
        if page_active not in PAGES:
            page_active = "Accueil"
        for page in PAGES:
            if st.button(
                page,
                key=f"navigation_{page}",
                type="primary" if page == page_active else "secondary",
                use_container_width=True,
            ):
                st.session_state["page_active"] = page
                st.rerun()
    return page_active
