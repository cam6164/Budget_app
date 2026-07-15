import streamlit as st

from src.navigation import recharger_page


def afficher(_parametres: dict) -> None:
    st.title("Accueil")
    st.subheader("Votre espace personnel, simple et entièrement local")
    col_budget, col_courses = st.columns(2, gap="large")
    with col_budget:
        st.markdown(
            """<div class="budget-card"><h3>Suivi budget et finances</h3>
            <p>Transactions, budget mensuel, épargne et indicateurs.</p>
            <p><strong>Actif</strong></p></div>""",
            unsafe_allow_html=True,
        )
        if st.button("Ouvrir le suivi budget", type="primary", width="stretch"):
            recharger_page("Tableau de bord")
    with col_courses:
        st.markdown(
            """<div class="budget-card"><h3>Courses et recettes</h3>
            <p>Planification des repas et liste de courses.</p>
            <p><strong>À venir</strong></p></div>""",
            unsafe_allow_html=True,
        )
        st.button("Disponible dans une future version", disabled=True, width="stretch")
