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
    if "sidebar_open" not in st.session_state:
        st.session_state["sidebar_open"] = True
    sidebar_ouverte = bool(st.session_state["sidebar_open"])
    if not sidebar_ouverte:
        st.markdown(
            """<style>
            [data-testid="stSidebar"] { display: none !important; }
            .st-key-sidebar_reopen {
                position: fixed !important;
                left: 0 !important;
                top: calc(50vh - 1.5rem) !important;
                z-index: 2147483647 !important;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                width: 2.65rem !important;
                height: 3rem !important;
                margin: 0 !important;
                overflow: visible !important;
            }
            .st-key-sidebar_reopen button {
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                align-items: center !important;
                justify-content: center !important;
                min-height: 3rem !important;
                height: 3rem !important;
                width: 2.65rem !important;
                padding: 0 !important;
                border: 1px solid var(--app-principale) !important;
                border-left: 0 !important;
                border-radius: 0 10px 10px 0 !important;
                font-size: 1.3rem !important;
                background: var(--app-principale) !important;
                color: var(--app-fond) !important;
                box-shadow: 0 5px 18px rgba(0,0,0,.45) !important;
            }
            .st-key-sidebar_reopen button p,
            .st-key-sidebar_reopen button span {
                color: var(--app-fond) !important;
            }
            </style>""",
            unsafe_allow_html=True,
        )
        if st.button("☰", key="sidebar_reopen", help="Ouvrir le menu"):
            st.session_state["sidebar_open"] = True
            recharger_page(page_active)
        return page_active

    with st.sidebar:
        col_titre, col_fermer = st.columns([5, 1], vertical_alignment="center")
        col_titre.markdown("### Budget personnel")
        if col_fermer.button("‹", key="sidebar_close", help="Fermer le menu"):
            st.session_state["sidebar_open"] = False
            recharger_page(page_active)
        for page in PAGES:
            if st.button(
                page,
                key=f"navigation_{page}",
                type="primary" if page == page_active else "secondary",
                use_container_width=True,
            ):
                recharger_page(page)
    return page_active
