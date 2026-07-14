import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from src.config import (
    CATEGORIES_DEFAUT,
    DATABASE_PATH,
    DATA_DIR,
    PARAMETRES_DEFAUT,
    SCHEMA_PATH,
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

