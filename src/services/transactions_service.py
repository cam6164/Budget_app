from datetime import date

from src.database import connexion_db, maintenant
from src.utils import mois_budget_automatique, mois_canonique


def normaliser_montants(
    type_transaction: str,
    categorie: str | None,
    sens_remboursement: str | None,
    montant: float,
) -> tuple[float, float]:
    montant = abs(float(montant))
    if type_transaction == "Revenu":
        return montant, montant
    if type_transaction == "Dépense":
        return -montant, montant
    if type_transaction == "Épargne":
        if categorie and "retrait" in categorie.lower():
            return montant, -montant
        return -montant, montant
    if type_transaction == "Remboursement":
        if sens_remboursement == "On me rembourse":
            return montant, -montant
        if sens_remboursement == "Je rembourse quelqu’un":
            return -montant, montant
        raise ValueError("Le sens du remboursement est obligatoire.")
    raise ValueError("Type de transaction non reconnu.")


def ajouter_transaction(
    date_reelle: date,
    type_transaction: str,
    categorie: str | None,
    libelle: str,
    montant: float,
    moyen_paiement: str | None = None,
    mois_budget: str | None = None,
    commentaire: str | None = None,
    sens_remboursement: str | None = None,
    categorie_remboursee: str | None = None,
) -> int:
    if not libelle.strip():
        raise ValueError("Le libellé est obligatoire.")
    if float(montant) <= 0:
        raise ValueError("Le montant doit être strictement positif.")
    if type_transaction == "Remboursement" and not categorie_remboursee:
        raise ValueError("La catégorie remboursée est obligatoire.")

    mois_reel = mois_canonique(date_reelle)
    mois_budget = mois_canonique(mois_budget) if mois_budget else mois_budget_automatique(
        date_reelle, type_transaction, categorie, libelle
    )
    bancaire, budget = normaliser_montants(
        type_transaction, categorie, sens_remboursement, montant
    )
    horodatage = maintenant()
    with connexion_db() as connexion:
        curseur = connexion.execute(
            """INSERT INTO transactions (
                   date_reelle, mois_reel, mois_budget, type, sens_remboursement,
                   categorie, categorie_remboursee, libelle, montant_bancaire,
                   montant_budget, moyen_paiement, commentaire, source,
                   created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'manuel', ?, ?)""",
            (
                date_reelle.isoformat(), mois_reel, mois_budget, type_transaction,
                sens_remboursement, categorie, categorie_remboursee, libelle.strip(),
                bancaire, budget, moyen_paiement, commentaire, horodatage, horodatage,
            ),
        )
        return int(curseur.lastrowid)


def lister_transactions(
    mois_budget: str | None = None,
    type_transaction: str | None = None,
    categorie: str | None = None,
    recherche: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    parametres: list[object] = []
    if mois_budget:
        clauses.append("mois_budget = ?")
        parametres.append(mois_canonique(mois_budget))
    if type_transaction:
        clauses.append("type = ?")
        parametres.append(type_transaction)
    if categorie:
        clauses.append("(categorie = ? OR categorie_remboursee = ?)")
        parametres.extend([categorie, categorie])
    if recherche:
        clauses.append("LOWER(libelle) LIKE ?")
        parametres.append(f"%{recherche.lower()}%")
    sql = "SELECT * FROM transactions"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date_reelle DESC, id DESC"
    with connexion_db() as connexion:
        lignes = connexion.execute(sql, parametres).fetchall()
    return [dict(ligne) for ligne in lignes]


def supprimer_transaction(transaction_id: int) -> bool:
    with connexion_db() as connexion:
        curseur = connexion.execute(
            "DELETE FROM transactions WHERE id = ?", (int(transaction_id),)
        )
    return curseur.rowcount > 0


def supprimer_transactions(transaction_ids: list[int]) -> int:
    """Supprime en une fois les transactions sélectionnées après sauvegarde."""
    from src.services.backup_service import creer_sauvegarde

    identifiants = sorted({int(transaction_id) for transaction_id in transaction_ids})
    if not identifiants:
        return 0
    marqueurs = ", ".join("?" for _ in identifiants)
    with connexion_db() as connexion:
        nombre = connexion.execute(
            f"SELECT COUNT(*) FROM transactions WHERE id IN ({marqueurs})",
            identifiants,
        ).fetchone()[0]
    if nombre == 0:
        return 0
    creer_sauvegarde(
        f"Sauvegarde automatique avant suppression de {nombre} transaction(s)"
    )
    with connexion_db() as connexion:
        curseur = connexion.execute(
            f"DELETE FROM transactions WHERE id IN ({marqueurs})",
            identifiants,
        )
    return int(curseur.rowcount)


def modifier_transactions(transactions: list[dict]) -> int:
    """Valide puis enregistre un lot de modifications après sauvegarde locale."""
    from src.services.backup_service import creer_sauvegarde
    from src.services.import_bancaire_service import normaliser_date, normaliser_montant

    lignes: list[dict] = []
    for index, transaction in enumerate(transactions, start=1):
        try:
            date_reelle = normaliser_date(transaction["date_reelle"])
            type_transaction = str(transaction["type"]).strip()
            if type_transaction not in ("Revenu", "Dépense", "Épargne", "Remboursement"):
                raise ValueError("type non reconnu")
            libelle = str(transaction["libelle"]).strip()
            if not libelle:
                raise ValueError("libellé obligatoire")
            sens = str(transaction.get("sens_remboursement", "") or "").strip()
            categorie_remboursee = str(
                transaction.get("categorie_remboursee", "") or ""
            ).strip()
            if type_transaction == "Remboursement" and (
                sens not in ("On me rembourse", "Je rembourse quelqu’un")
                or not categorie_remboursee
            ):
                raise ValueError("remboursement incomplet")
            lignes.append(
                {
                    "id": int(transaction["id"]),
                    "date_reelle": date_reelle.isoformat(),
                    "mois_reel": mois_canonique(date_reelle),
                    "mois_budget": mois_canonique(str(transaction["mois_budget"])),
                    "type": type_transaction,
                    "sens": sens or None,
                    "categorie": str(transaction.get("categorie", "") or "").strip() or None,
                    "categorie_remboursee": categorie_remboursee or None,
                    "libelle": libelle,
                    "montant_bancaire": normaliser_montant(transaction["montant_bancaire"]),
                    "montant_budget": normaliser_montant(transaction["montant_budget"]),
                    "moyen_paiement": str(transaction.get("moyen_paiement", "") or "").strip() or None,
                    "commentaire": str(transaction.get("commentaire", "") or ""),
                }
            )
        except Exception as erreur:
            raise ValueError(f"Ligne {index} invalide : {erreur}") from erreur
    if not lignes:
        return 0
    creer_sauvegarde("Sauvegarde automatique avant modification des transactions")
    horodatage = maintenant()
    with connexion_db() as connexion:
        for ligne in lignes:
            curseur = connexion.execute(
                """UPDATE transactions SET
                       date_reelle = ?, mois_reel = ?, mois_budget = ?, type = ?,
                       sens_remboursement = ?, categorie = ?, categorie_remboursee = ?,
                       libelle = ?, montant_bancaire = ?, montant_budget = ?,
                       moyen_paiement = ?, commentaire = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    ligne["date_reelle"], ligne["mois_reel"], ligne["mois_budget"],
                    ligne["type"], ligne["sens"], ligne["categorie"],
                    ligne["categorie_remboursee"], ligne["libelle"],
                    ligne["montant_bancaire"], ligne["montant_budget"],
                    ligne["moyen_paiement"], ligne["commentaire"], horodatage,
                    ligne["id"],
                ),
            )
            if curseur.rowcount == 0:
                raise ValueError(f"Transaction n°{ligne['id']} introuvable.")
    return len(lignes)


def mois_disponibles() -> list[str]:
    with connexion_db() as connexion:
        lignes = connexion.execute(
            "SELECT DISTINCT mois_budget FROM transactions ORDER BY mois_budget"
        ).fetchall()
    return [ligne[0] for ligne in lignes]
