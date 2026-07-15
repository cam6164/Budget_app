import streamlit as st


PAGES = [
    "Accueil", "Tableau de bord", "Transactions", "Import bancaire", "Budget mensuel",
    "Épargne", "Catégories", "Paramètres",
]

PAGE_ACTIVE_KEY = "page_active"


def definir_page_active(page: str) -> None:
    if page not in PAGES:
        raise ValueError(f"Page inconnue : {page}")
    st.session_state[PAGE_ACTIVE_KEY] = page


def recharger_page(page: str) -> None:
    """Relance Streamlit en garantissant que la page métier reste active."""
    definir_page_active(page)
    st.session_state["navigation_cible"] = page
    st.rerun()


def afficher_navigation() -> str:
    cible = st.session_state.pop("navigation_cible", None)
    if cible in PAGES:
        definir_page_active(cible)
    page_active = st.session_state.get(PAGE_ACTIVE_KEY, "Accueil")
    if page_active not in PAGES:
        page_active = "Accueil"
        definir_page_active(page_active)
    st.markdown(
        """<style>
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            transform: translateX(0) !important;
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown("### Budget personnel")
        for page in PAGES:
            if st.button(
                page,
                key=f"navigation_{page}",
                type="primary" if page == page_active else "secondary",
                use_container_width=True,
            ):
                recharger_page(page)
    return page_active
