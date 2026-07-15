import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from src.config import (
    CATEGORIES_DEFAUT,
    DATABASE_PATH,
    DATA_DIR,
    PARAMETRES_DEFAUT,
    REGLES_AFFECTATION_DEFAUT,
    SCHEMA_PATH,
    THEMES_AUTORISES,
)


def maintenant() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connexion = sqlite3.connect(DATABASE_PATH, timeout=20)
    connexion.row_factory = sqlite3.Row
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion


@contextmanager
def connexion_db() -> Iterator[sqlite3.Connection]:
    connexion = get_connection()
    try:
        yield connexion
        connexion.commit()
    except Exception:
        connexion.rollback()
        raise
    finally:
        connexion.close()


def initialiser_base() -> None:
    """Crée le schéma et les données de référence au premier lancement."""
    with connexion_db() as connexion:
        connexion.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        colonnes_transactions = {
            ligne["name"]
            for ligne in connexion.execute("PRAGMA table_info(transactions)").fetchall()
        }
        if "libelle_bancaire_brut" not in colonnes_transactions:
            connexion.execute(
                "ALTER TABLE transactions ADD COLUMN libelle_bancaire_brut TEXT"
            )
        nombre = connexion.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if nombre == 0:
            horodatage = maintenant()
            for type_categorie, categories in CATEGORIES_DEFAUT.items():
                for ordre, categorie in enumerate(categories, start=1):
                    connexion.execute(
                        """INSERT INTO categories
                           (type, categorie, actif, ordre, created_at, updated_at)
                           VALUES (?, ?, 1, ?, ?, ?)""",
                        (type_categorie, categorie, ordre, horodatage, horodatage),
                    )
        for cle, valeur in PARAMETRES_DEFAUT.items():
            connexion.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (cle, valeur),
            )
        theme_actuel = connexion.execute(
            "SELECT value FROM settings WHERE key = 'theme_actif'"
        ).fetchone()
        if not theme_actuel or theme_actuel["value"] not in THEMES_AUTORISES:
            connexion.execute(
                """INSERT INTO settings(key, value) VALUES ('theme_actif', 'Sombre bleu')
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value"""
            )
        affichage_actuel = connexion.execute(
            "SELECT value FROM settings WHERE key = 'configuration_affichage'"
        ).fetchone()
        if not affichage_actuel or affichage_actuel["value"] not in {
            "ecran_15", "ecran_27"
        }:
            connexion.execute(
                """INSERT INTO settings(key, value)
                   VALUES ('configuration_affichage', 'ecran_15')
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value"""
            )
        nombre_regles = connexion.execute(
            "SELECT COUNT(*) FROM regles_affectation"
        ).fetchone()[0]
        if nombre_regles == 0:
            horodatage = maintenant()
            for regle in REGLES_AFFECTATION_DEFAUT:
                connexion.execute(
                    """INSERT INTO regles_affectation (
                           mot_cle, type_attribue, categorie_attribuee,
                           sens_remboursement, categorie_remboursee, actif,
                           priorite, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                    (
                        regle["mot_cle"], regle["type_attribue"],
                        regle.get("categorie_attribuee", ""),
                        regle.get("sens_remboursement", ""),
                        regle.get("categorie_remboursee", ""),
                        regle["priorite"], horodatage, horodatage,
                    ),
                )


def lire_parametres() -> dict[str, str]:
    with connexion_db() as connexion:
        lignes = connexion.execute("SELECT key, value FROM settings").fetchall()
    return {ligne["key"]: ligne["value"] for ligne in lignes}


def enregistrer_parametres(parametres: dict[str, str | float]) -> None:
    with connexion_db() as connexion:
        for cle, valeur in parametres.items():
            connexion.execute(
                """INSERT INTO settings(key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (cle, str(valeur)),
            )
