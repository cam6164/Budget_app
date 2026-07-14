import re
import unicodedata

from src.config import TYPES_TRANSACTION
from src.database import connexion_db, maintenant


def normaliser_texte(texte: object) -> str:
    """Normalise casse, accents et espaces pour les recherches bancaires."""
    valeur = "" if texte is None else str(texte)
    valeur = unicodedata.normalize("NFD", valeur)
    valeur = "".join(
        caractere for caractere in valeur
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"\s+", " ", valeur.upper()).strip()


def lister_regles(actives_uniquement: bool = False) -> list[dict]:
    sql = "SELECT * FROM regles_affectation"
    if actives_uniquement:
        sql += " WHERE actif = 1"
    sql += " ORDER BY priorite, id"
    with connexion_db() as connexion:
        lignes = connexion.execute(sql).fetchall()
    return [dict(ligne) for ligne in lignes]


def trouver_regle(libelle: str) -> dict | None:
    libelle_normalise = normaliser_texte(libelle)
    for regle in lister_regles(actives_uniquement=True):
        mot_cle = normaliser_texte(regle["mot_cle"])
        if mot_cle and mot_cle in libelle_normalise:
            return regle
    return None


def appliquer_regle(libelle: str, montant_bancaire: float) -> dict:
    regle = trouver_regle(libelle)
    if regle:
        incomplete = (
            regle["type_attribue"] == "Remboursement"
            and (not regle["sens_remboursement"] or not regle["categorie_remboursee"])
        )
        return {
            "type": regle["type_attribue"],
            "categorie": regle["categorie_attribuee"] or "",
            "sens_remboursement": regle["sens_remboursement"] or "",
            "categorie_remboursee": regle["categorie_remboursee"] or "",
            "statut_import": "À vérifier" if incomplete else "Validée",
            "regle_id": regle["id"],
        }
    return {
        "type": "Dépense" if float(montant_bancaire) < 0 else "Revenu",
        "categorie": "",
        "sens_remboursement": "",
        "categorie_remboursee": "",
        "statut_import": "À vérifier",
        "regle_id": None,
    }


def ajouter_regle(
    mot_cle: str,
    type_attribue: str,
    categorie_attribuee: str = "",
    sens_remboursement: str = "",
    categorie_remboursee: str = "",
    actif: bool = True,
    priorite: int = 100,
) -> int:
    mot_cle = normaliser_texte(mot_cle)
    if not mot_cle:
        raise ValueError("Le mot-clé est obligatoire.")
    if type_attribue not in TYPES_TRANSACTION:
        raise ValueError("Le type attribué n’est pas reconnu.")
    horodatage = maintenant()
    with connexion_db() as connexion:
        curseur = connexion.execute(
            """INSERT INTO regles_affectation (
                   mot_cle, type_attribue, categorie_attribuee,
                   sens_remboursement, categorie_remboursee, actif,
                   priorite, created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mot_cle, type_attribue, categorie_attribuee or "",
                sens_remboursement or "", categorie_remboursee or "",
                int(actif), int(priorite), horodatage, horodatage,
            ),
        )
        return int(curseur.lastrowid)


def modifier_regle(
    regle_id: int,
    mot_cle: str,
    type_attribue: str,
    categorie_attribuee: str = "",
    sens_remboursement: str = "",
    categorie_remboursee: str = "",
    actif: bool = True,
    priorite: int = 100,
) -> None:
    mot_cle = normaliser_texte(mot_cle)
    if not mot_cle:
        raise ValueError("Le mot-clé est obligatoire.")
    if type_attribue not in TYPES_TRANSACTION:
        raise ValueError("Le type attribué n’est pas reconnu.")
    with connexion_db() as connexion:
        curseur = connexion.execute(
            """UPDATE regles_affectation SET
                   mot_cle = ?, type_attribue = ?, categorie_attribuee = ?,
                   sens_remboursement = ?, categorie_remboursee = ?, actif = ?,
                   priorite = ?, updated_at = ?
               WHERE id = ?""",
            (
                mot_cle, type_attribue, categorie_attribuee or "",
                sens_remboursement or "", categorie_remboursee or "",
                int(actif), int(priorite), maintenant(), int(regle_id),
            ),
        )
        if curseur.rowcount == 0:
            raise ValueError("Règle introuvable.")


def supprimer_regle(regle_id: int) -> bool:
    with connexion_db() as connexion:
        curseur = connexion.execute(
            "DELETE FROM regles_affectation WHERE id = ?", (int(regle_id),)
        )
    return curseur.rowcount > 0

