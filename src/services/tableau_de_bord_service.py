from src.database import connexion_db
from src.services.budget_service import rapport_budget
from src.services.epargne_service import tableau_epargne
from src.utils import ajouter_mois, euros, jours_du_mois, mois_canonique


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


def _mois_avec_donnees() -> list[str]:
    with connexion_db() as connexion:
        lignes = connexion.execute(
            """SELECT mois FROM budgets
               UNION SELECT mois_budget AS mois FROM transactions
               ORDER BY mois"""
        ).fetchall()
    return [ligne["mois"] for ligne in lignes]


def historique_mensuel(solde_initial: float = 0) -> list[dict]:
    mois_connus = _mois_avec_donnees()
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
    for mois in mois_connus:
        valeurs = groupes.get(mois, {})
        revenus = valeurs.get("Revenu", 0.0)
        depenses = valeurs.get("Dépense", 0.0) + valeurs.get("Remboursement", 0.0)
        epargne = valeurs.get("Épargne", 0.0)
        resultat.append(
            {
                "mois": mois,
                "revenus": revenus,
                "depenses": depenses,
                "epargne_nette": epargne,
                "reste_disponible": revenus - depenses - epargne,
                "equilibre": revenus - depenses - epargne,
                "taux_epargne": epargne / revenus if revenus > 0 else 0.0,
                "solde_epargne": epargne_par_mois.get(mois, {}).get("solde_fin", solde_initial),
            }
        )
    return resultat


def depenses_cumulees(mois: str) -> list[dict]:
    """Retourne le réel jusqu'au dernier mouvement et le budget théorique jusqu'à la fin."""
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
        budget = float(
            connexion.execute(
                """SELECT COALESCE(SUM(budget_prevu), 0) FROM budgets
                   WHERE mois = ? AND type = 'Dépense'""",
                (mois,),
            ).fetchone()[0]
        )
    par_jour = {int(ligne["jour"]): float(ligne["total"] or 0) for ligne in lignes}
    dernier_jour = max(par_jour, default=0)
    nombre_jours = jours_du_mois(mois)
    cumul = 0.0
    resultat: list[dict] = []
    for jour in range(1, nombre_jours + 1):
        cumul += par_jour.get(jour, 0.0)
        resultat.append(
            {
                "jour": jour,
                "depenses_cumulees": cumul if jour <= dernier_jour else None,
                "budget_theorique": budget * jour / nombre_jours,
            }
        )
    return resultat


def comparaison_categories(mois: str) -> list[dict]:
    resultat = []
    for ligne in rapport_budget(mois):
        if ligne["type"] != "Dépense":
            continue
        if ligne["budget_prevu"] == 0 and ligne["reel"] == 0:
            continue
        copie = dict(ligne)
        copie["depassement"] = ligne["reel"] > ligne["budget_prevu"]
        resultat.append(copie)
    return resultat


def alertes_budget(
    mois: str,
    seuil_vigilance: float = 0.8,
    seuil_alerte: float = 1.0,
) -> list[dict]:
    alertes: list[dict] = []
    for ligne in comparaison_categories(mois):
        prevu = float(ligne["budget_prevu"])
        reel = float(ligne["reel"])
        categorie = ligne["categorie"]
        if prevu == 0 and reel > 0:
            alertes.append(
                {
                    "niveau": "alerte",
                    "type": "aucun_budget",
                    "categorie": categorie,
                    "message": f"Dépense enregistrée sur {categorie} alors qu’aucun budget n’est prévu.",
                }
            )
            continue
        pourcentage = reel / prevu if prevu > 0 else 0.0
        if prevu > 0 and reel > prevu:
            alertes.append(
                {
                    "niveau": "depassement",
                    "type": "depassement",
                    "categorie": categorie,
                    "message": (
                        f"Budget dépassé pour {categorie} : {euros(reel)} dépensés "
                        f"pour {euros(prevu)} prévus."
                    ),
                }
            )
        elif prevu > 0 and pourcentage >= seuil_vigilance:
            alertes.append(
                {
                    "niveau": "alerte" if pourcentage >= seuil_alerte else "vigilance",
                    "type": "vigilance",
                    "categorie": categorie,
                    "message": f"Vigilance sur {categorie} : {pourcentage:.0%} du budget utilisé.",
                }
            )
    if indicateurs(mois)["reste_disponible"] < 0:
        alertes.append(
            {
                "niveau": "depassement",
                "type": "reste_negatif",
                "categorie": None,
                "message": "Reste disponible négatif ce mois-ci.",
            }
        )
    if not alertes:
        return [
            {
                "niveau": "ok", "type": "aucune", "categorie": None,
                "message": "Aucune alerte budget pour ce mois.",
            }
        ]
    return alertes


def comparaison_mois_precedent(mois: str) -> dict:
    mois = mois_canonique(mois)
    mois_precedent = ajouter_mois(mois, -1)
    courant = indicateurs(mois)
    precedent = indicateurs(mois_precedent)
    disponible = mois_precedent in _mois_avec_donnees()
    cles = ["revenus", "depenses", "epargne_nette", "reste_disponible", "taux_epargne"]
    ecarts = {cle: courant[cle] - precedent[cle] for cle in cles}
    evolutions = {
        cle: (ecarts[cle] / abs(precedent[cle]) if precedent[cle] != 0 else None)
        for cle in cles
    }
    return {
        "disponible": disponible,
        "mois": mois,
        "mois_precedent": mois_precedent,
        "courant": courant,
        "precedent": precedent,
        "ecarts": ecarts,
        "evolutions": evolutions,
    }


def phrases_comparatif(comparatif: dict) -> list[str]:
    if not comparatif["disponible"]:
        return ["Pas encore de données pour le mois précédent."]
    phrases = []
    variation_depenses = comparatif["ecarts"]["depenses"]
    if abs(variation_depenses) < 0.01:
        phrases.append("Dépenses stables par rapport au mois précédent.")
    else:
        direction = "hausse" if variation_depenses > 0 else "baisse"
        phrases.append(
            f"Dépenses en {direction} de {euros(abs(variation_depenses))} par rapport au mois précédent."
        )
    variation_epargne = comparatif["ecarts"]["epargne_nette"]
    if abs(variation_epargne) < 0.01:
        phrases.append("Épargne nette stable.")
    else:
        direction = "hausse" if variation_epargne > 0 else "baisse"
        phrases.append(f"Épargne nette en {direction} de {euros(abs(variation_epargne))}.")
    variation_taux = comparatif["ecarts"]["taux_epargne"]
    if abs(variation_taux) < 0.001:
        phrases.append("Taux d’épargne stable.")
    return phrases


def resume_automatique(
    mois: str,
    seuil_vigilance: float = 0.8,
    seuil_alerte: float = 1.0,
) -> list[str]:
    kpi = indicateurs(mois)
    alertes = alertes_budget(mois, seuil_vigilance, seuil_alerte)
    depassements = [alerte for alerte in alertes if alerte["type"] == "depassement"]
    phrases: list[str] = []
    if depassements:
        phrases.append(
            "Attention, plusieurs catégories dépassent leur budget."
            if len(depassements) > 1
            else "Attention, une catégorie dépasse son budget."
        )
    elif kpi["depenses"] <= kpi["budget_depenses"]:
        phrases.append("Ce mois-ci, les dépenses restent inférieures au budget prévu.")
    if kpi["epargne_nette"] > 0:
        phrases.append("L’épargne nette est positive ce mois-ci.")
    elif kpi["epargne_nette"] < 0:
        phrases.append("L’épargne nette est négative ce mois-ci.")
    if kpi["reste_disponible"] < 0:
        phrases.append("Le reste disponible est négatif, il faut surveiller les prochaines dépenses.")
    comparatif = comparaison_mois_precedent(mois)
    if comparatif["disponible"] and comparatif["ecarts"]["depenses"] > 0:
        phrases.append("Les dépenses ont augmenté par rapport au mois précédent.")
    return phrases or ["Les données du mois sont prêtes à être analysées."]
