from src.database import connexion_db
from src.services.budget_service import rapport_budget
from src.services.epargne_service import tableau_epargne
from src.utils import ajouter_mois, mois_canonique


def indicateurs(mois: str) -> dict[str, float]:
    mois = mois_canonique(mois)
    with connexion_db() as connexion:
        totaux = connexion.execute(
            """SELECT type, SUM(montant_budget) AS total FROM transactions
               WHERE mois_budget = ? GROUP BY type""",
            (mois,),
        ).fetchall()
        budget_depenses = connexion.execute(
            """SELECT COALESCE(SUM(budget_prevu), 0) FROM budgets
               WHERE mois = ? AND type = 'Dépense'""",
            (mois,),
        ).fetchone()[0]
    par_type = {ligne["type"]: float(ligne["total"] or 0) for ligne in totaux}
    revenus = par_type.get("Revenu", 0.0)
    depenses = par_type.get("Dépense", 0.0) + par_type.get("Remboursement", 0.0)
    epargne = par_type.get("Épargne", 0.0)
    return {
        "revenus": revenus,
        "budget_depenses": float(budget_depenses),
        "depenses": depenses,
        "reste_disponible": revenus - depenses - epargne,
        "epargne_nette": epargne,
        "taux_epargne": epargne / revenus if revenus > 0 else 0.0,
    }


def historique_mensuel(solde_initial: float = 0) -> list[dict]:
    with connexion_db() as connexion:
        lignes = connexion.execute(
            """SELECT mois_budget AS mois, type, SUM(montant_budget) AS total
               FROM transactions GROUP BY mois_budget, type ORDER BY mois_budget"""
        ).fetchall()
    groupes: dict[str, dict[str, float]] = {}
    for ligne in lignes:
        groupes.setdefault(ligne["mois"], {})[ligne["type"]] = float(ligne["total"] or 0)
    epargne_par_mois = {ligne["mois"]: ligne for ligne in tableau_epargne(solde_initial)}
    resultat = []
    for mois, valeurs in sorted(groupes.items()):
        revenus = valeurs.get("Revenu", 0.0)
        depenses = valeurs.get("Dépense", 0.0) + valeurs.get("Remboursement", 0.0)
        epargne = valeurs.get("Épargne", 0.0)
        resultat.append(
            {
                "mois": mois, "revenus": revenus, "depenses": depenses,
                "equilibre": revenus - depenses - epargne,
                "taux_epargne": epargne / revenus if revenus > 0 else 0.0,
                "solde_epargne": epargne_par_mois.get(mois, {}).get("solde_fin", solde_initial),
            }
        )
    return resultat


def depenses_cumulees(mois: str) -> list[dict]:
    mois = mois_canonique(mois)
    with connexion_db() as connexion:
        lignes = connexion.execute(
            """SELECT CAST(substr(date_reelle, 9, 2) AS INTEGER) AS jour,
                      SUM(montant_budget) AS total
               FROM transactions
               WHERE mois_budget = ? AND type IN ('Dépense', 'Remboursement')
               GROUP BY jour ORDER BY jour""",
            (mois,),
        ).fetchall()
    cumul = 0.0
    resultat = []
    for ligne in lignes:
        cumul += float(ligne["total"] or 0)
        resultat.append({"jour": ligne["jour"], "depenses_cumulees": cumul})
    return resultat


def comparaison_categories(mois: str) -> list[dict]:
    return [ligne for ligne in rapport_budget(mois) if ligne["type"] == "Dépense"]


def alertes_budget(mois: str, seuil_vigilance: float, seuil_alerte: float) -> list[dict]:
    return [
        ligne for ligne in rapport_budget(mois, seuil_vigilance, seuil_alerte)
        if ligne["type"] == "Dépense" and ligne["statut"] != "OK"
    ]


def comparaison_mois_precedent(mois: str) -> dict[str, float]:
    courant = indicateurs(mois)
    precedent = indicateurs(ajouter_mois(mois, -1))
    return {
        "depenses_courantes": courant["depenses"],
        "depenses_precedentes": precedent["depenses"],
        "variation": courant["depenses"] - precedent["depenses"],
    }

