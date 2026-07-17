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
        [data-testid="stMain"] {
            box-sizing: border-box !important;
            padding-left: 220px !important;
        }
        .st-key-navigation_fixe {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;
            z-index: 2147483000 !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 220px !important;
            min-width: 220px !important;
            max-width: 220px !important;
            height: 100vh !important;
            padding: .8rem .6rem !important;
            overflow-y: auto !important;
            background: var(--app-carte) !important;
            border-right: 1px solid var(--app-bordure) !important;
            box-shadow: 8px 0 24px rgba(0,0,0,.2) !important;
        }
        .st-key-navigation_fixe h3 {
            margin: .15rem 0 .7rem !important;
            font-size: 1.05rem !important;
            color: var(--app-texte) !important;
        }
        .st-key-navigation_fixe [data-testid="stVerticalBlock"] {
            gap: .32rem !important;
        }
        .st-key-navigation_fixe .stButton > button {
            width: 100% !important;
            min-height: 2.55rem !important;
            justify-content: flex-start !important;
            border-radius: 7px !important;
            margin: .04rem 0 !important;
            padding-left: .7rem !important;
            padding-right: .55rem !important;
            font-size: .9rem !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    with st.container(key="navigation_fixe"):
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
