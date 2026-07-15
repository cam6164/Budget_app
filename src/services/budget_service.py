from src.database import connexion_db, maintenant
from src.utils import ajouter_mois, mois_canonique


def mois_budget_disponibles() -> list[str]:
    with connexion_db() as connexion:
        lignes = connexion.execute(
            "SELECT DISTINCT mois FROM budgets ORDER BY mois"
        ).fetchall()
    return [ligne[0] for ligne in lignes]


def creer_budget_mensuel(mois: str, copier_depuis: str | None = None) -> int:
    mois = mois_canonique(mois)
    valeurs_source: dict[tuple[str, str], float] = {}
    horodatage = maintenant()
    with connexion_db() as connexion:
        if copier_depuis:
            lignes = connexion.execute(
                "SELECT type, categorie, budget_prevu FROM budgets WHERE mois = ?",
                (mois_canonique(copier_depuis),),
            ).fetchall()
            valeurs_source = {
                (ligne["type"], ligne["categorie"]): ligne["budget_prevu"]
                for ligne in lignes
            }
        categories = connexion.execute(
            """SELECT type, categorie FROM categories
               WHERE actif = 1 AND type IN ('Revenu', 'Dépense', 'Épargne')
               ORDER BY type, ordre"""
        ).fetchall()
        ajoutees = 0
        for categorie in categories:
            budget = valeurs_source.get(
                (categorie["type"], categorie["categorie"]), 0.0
            )
            curseur = connexion.execute(
                """INSERT OR IGNORE INTO budgets
                   (mois, type, categorie, budget_prevu, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    mois, categorie["type"], categorie["categorie"], budget,
                    horodatage, horodatage,
                ),
            )
            ajoutees += curseur.rowcount
    return ajoutees


def creer_mois_suivant() -> str:
    mois = mois_budget_disponibles()
    if not mois:
        raise ValueError("Créez d’abord un premier budget.")
    suivant = ajouter_mois(mois[-1], 1)
    creer_budget_mensuel(suivant, mois[-1])
    return suivant


def supprimer_mois_budget(mois: str) -> int:
    """Supprime uniquement les lignes de budget du mois, jamais les transactions."""
    from src.services.backup_service import creer_sauvegarde

    mois = mois_canonique(mois)
    with connexion_db() as connexion:
        nombre = connexion.execute(
            "SELECT COUNT(*) FROM budgets WHERE mois = ?", (mois,)
        ).fetchone()[0]
    if nombre == 0:
        return 0
    creer_sauvegarde(f"Sauvegarde automatique avant suppression du budget {mois}")
    with connexion_db() as connexion:
        curseur = connexion.execute("DELETE FROM budgets WHERE mois = ?", (mois,))
    return int(curseur.rowcount)


def enregistrer_budgets(valeurs: list[dict]) -> None:
    horodatage = maintenant()
    with connexion_db() as connexion:
        for ligne in valeurs:
            connexion.execute(
                """UPDATE budgets SET budget_prevu = ?, updated_at = ?
                   WHERE id = ?""",
                (max(0.0, float(ligne["budget_prevu"])), horodatage, int(ligne["id"])),
            )


def rapport_budget(
    mois: str,
    seuil_vigilance: float = 0.8,
    seuil_alerte: float = 1.0,
) -> list[dict]:
    mois = mois_canonique(mois)
    with connexion_db() as connexion:
        budgets = connexion.execute(
            """SELECT id, mois, type, categorie, budget_prevu FROM budgets
               WHERE mois = ?
               ORDER BY CASE type WHEN 'Revenu' THEN 1 WHEN 'Dépense' THEN 2 ELSE 3 END,
                        categorie""",
            (mois,),
        ).fetchall()
        transactions = connexion.execute(
            """SELECT type, categorie, categorie_remboursee, montant_budget
               FROM transactions WHERE mois_budget = ?""",
            (mois,),
        ).fetchall()

    reels: dict[tuple[str, str], float] = {}
    for transaction in transactions:
        if transaction["type"] in ("Revenu", "Dépense", "Épargne"):
            cle = (transaction["type"], transaction["categorie"])
        elif transaction["type"] == "Remboursement":
            cle = ("Dépense", transaction["categorie_remboursee"])
        else:
            continue
        reels[cle] = reels.get(cle, 0.0) + float(transaction["montant_budget"])

    resultat: list[dict] = []
    for budget in budgets:
        prevu = float(budget["budget_prevu"])
        reel = reels.get((budget["type"], budget["categorie"]), 0.0)
        ecart = prevu - reel if budget["type"] == "Dépense" else reel - prevu
        pourcentage = reel / prevu if prevu > 0 else 0.0
        if budget["type"] == "Revenu":
            statut = "OK" if reel >= prevu else "Vigilance"
        elif pourcentage >= seuil_alerte:
            statut = "Dépassement"
        elif pourcentage >= seuil_vigilance:
            statut = "Vigilance"
        else:
            statut = "OK"
        resultat.append(
            {
                "id": budget["id"], "mois": mois, "type": budget["type"],
                "categorie": budget["categorie"], "budget_prevu": prevu,
                "reel": reel, "ecart": ecart, "pourcentage_utilise": pourcentage,
                "statut": statut,
            }
        )
    return resultat
