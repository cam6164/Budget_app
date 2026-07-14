from src.database import connexion_db


def tableau_epargne(solde_initial: float) -> list[dict]:
    with connexion_db() as connexion:
        mois = connexion.execute(
            """SELECT mois FROM budgets
               UNION SELECT mois_budget AS mois FROM transactions
               ORDER BY mois"""
        ).fetchall()
        transactions = connexion.execute(
            """SELECT mois_budget, type, SUM(montant_budget) AS total
               FROM transactions WHERE type IN ('Revenu', 'Épargne')
               GROUP BY mois_budget, type"""
        ).fetchall()
        budgets = connexion.execute(
            """SELECT mois, SUM(budget_prevu) AS total FROM budgets
               WHERE type = 'Épargne' GROUP BY mois"""
        ).fetchall()
    totaux = {(ligne["mois_budget"], ligne["type"]): float(ligne["total"] or 0) for ligne in transactions}
    prevus = {ligne["mois"]: float(ligne["total"] or 0) for ligne in budgets}
    solde = float(solde_initial)
    resultat: list[dict] = []
    for ligne_mois in mois:
        cle_mois = ligne_mois["mois"]
        revenus = totaux.get((cle_mois, "Revenu"), 0.0)
        epargne_reelle = totaux.get((cle_mois, "Épargne"), 0.0)
        epargne_prevue = prevus.get(cle_mois, 0.0)
        debut = solde
        solde = debut + epargne_reelle
        taux = epargne_reelle / revenus if revenus > 0 else 0.0
        resultat.append(
            {
                "mois": cle_mois, "revenus_reels": revenus,
                "epargne_prevue": epargne_prevue, "epargne_reelle": epargne_reelle,
                "ecart": epargne_reelle - epargne_prevue, "taux_epargne": taux,
                "solde_debut": debut, "solde_fin": solde,
                "statut": "OK" if epargne_reelle >= epargne_prevue else "Vigilance",
            }
        )
    return resultat

