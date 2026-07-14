from src.config import TYPES_TRANSACTION
from src.database import connexion_db, maintenant


def lister_categories(
    type_categorie: str | None = None, actifs_uniquement: bool = False
) -> list[dict]:
    clauses: list[str] = []
    parametres: list[object] = []
    if type_categorie:
        clauses.append("type = ?")
        parametres.append(type_categorie)
    if actifs_uniquement:
        clauses.append("actif = 1")
    sql = "SELECT * FROM categories"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY CASE type WHEN 'Revenu' THEN 1 WHEN 'Dépense' THEN 2 WHEN 'Épargne' THEN 3 ELSE 4 END, ordre, categorie"
    with connexion_db() as connexion:
        lignes = connexion.execute(sql, parametres).fetchall()
    return [dict(ligne) for ligne in lignes]


def noms_categories(type_categorie: str, actifs_uniquement: bool = True) -> list[str]:
    return [
        ligne["categorie"]
        for ligne in lister_categories(type_categorie, actifs_uniquement)
    ]


def ajouter_categorie(type_categorie: str, categorie: str, actif: bool = True) -> int:
    categorie = categorie.strip()
    if type_categorie not in TYPES_TRANSACTION:
        raise ValueError("Type de catégorie non reconnu.")
    if not categorie:
        raise ValueError("Le nom de la catégorie est obligatoire.")
    horodatage = maintenant()
    with connexion_db() as connexion:
        ordre = connexion.execute(
            "SELECT COALESCE(MAX(ordre), 0) + 1 FROM categories WHERE type = ?",
            (type_categorie,),
        ).fetchone()[0]
        try:
            curseur = connexion.execute(
                """INSERT INTO categories(type, categorie, actif, ordre, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (type_categorie, categorie, int(actif), ordre, horodatage, horodatage),
            )
        except Exception as erreur:
            if "UNIQUE" in str(erreur).upper():
                raise ValueError("Cette catégorie existe déjà pour ce type.") from erreur
            raise
        if actif and type_categorie in ("Revenu", "Dépense", "Épargne"):
            connexion.execute(
                """INSERT OR IGNORE INTO budgets
                   (mois, type, categorie, budget_prevu, created_at, updated_at)
                   SELECT DISTINCT mois, ?, ?, 0, ?, ? FROM budgets""",
                (type_categorie, categorie, horodatage, horodatage),
            )
        return int(curseur.lastrowid)


def modifier_categorie(
    categorie_id: int, nouveau_nom: str, actif: bool, ordre: int
) -> None:
    nouveau_nom = nouveau_nom.strip()
    if not nouveau_nom:
        raise ValueError("Le nom de la catégorie est obligatoire.")
    with connexion_db() as connexion:
        ancienne = connexion.execute(
            "SELECT type, categorie, actif FROM categories WHERE id = ?",
            (int(categorie_id),),
        ).fetchone()
        if not ancienne:
            raise ValueError("Catégorie introuvable.")
        connexion.execute(
            """UPDATE categories SET categorie = ?, actif = ?, ordre = ?, updated_at = ?
               WHERE id = ?""",
            (nouveau_nom, int(actif), int(ordre), maintenant(), int(categorie_id)),
        )
        if ancienne["categorie"] != nouveau_nom:
            connexion.execute(
                "UPDATE budgets SET categorie = ? WHERE type = ? AND categorie = ?",
                (nouveau_nom, ancienne["type"], ancienne["categorie"]),
            )
            connexion.execute(
                "UPDATE transactions SET categorie = ?, updated_at = ? WHERE categorie = ?",
                (nouveau_nom, maintenant(), ancienne["categorie"]),
            )
            if ancienne["type"] == "Dépense":
                connexion.execute(
                    """UPDATE transactions SET categorie_remboursee = ?, updated_at = ?
                       WHERE categorie_remboursee = ?""",
                    (nouveau_nom, maintenant(), ancienne["categorie"]),
                )
        if actif and not ancienne["actif"] and ancienne["type"] in ("Revenu", "Dépense", "Épargne"):
            horodatage = maintenant()
            connexion.execute(
                """INSERT OR IGNORE INTO budgets
                   (mois, type, categorie, budget_prevu, created_at, updated_at)
                   SELECT DISTINCT mois, ?, ?, 0, ?, ? FROM budgets""",
                (ancienne["type"], nouveau_nom, horodatage, horodatage),
            )


def supprimer_categorie(categorie_id: int) -> tuple[bool, str]:
    with connexion_db() as connexion:
        categorie = connexion.execute(
            "SELECT type, categorie FROM categories WHERE id = ?", (int(categorie_id),)
        ).fetchone()
        if not categorie:
            return False, "Catégorie introuvable."
        nom = categorie["categorie"]
        transactions = connexion.execute(
            """SELECT COUNT(*) FROM transactions
               WHERE categorie = ? OR categorie_remboursee = ?""",
            (nom, nom),
        ).fetchone()[0]
        budgets = connexion.execute(
            "SELECT COUNT(*) FROM budgets WHERE type = ? AND categorie = ?",
            (categorie["type"], nom),
        ).fetchone()[0]
        if transactions or budgets:
            connexion.execute(
                "UPDATE categories SET actif = 0, updated_at = ? WHERE id = ?",
                (maintenant(), int(categorie_id)),
            )
            return False, "Catégorie utilisée : elle a été désactivée au lieu d’être supprimée."
        connexion.execute("DELETE FROM categories WHERE id = ?", (int(categorie_id),))
        return True, "Catégorie supprimée définitivement."
