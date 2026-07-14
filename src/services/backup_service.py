import shutil
from datetime import datetime
from pathlib import Path

from src.config import BACKUPS_DIR, DATABASE_PATH, EXPORTS_DIR
from src.database import connexion_db, maintenant
from src.services.transactions_service import lister_transactions


def creer_sauvegarde(commentaire: str = "Sauvegarde manuelle") -> Path:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("La base de données n’existe pas encore.")
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = BACKUPS_DIR / f"budget_{horodatage}.db"
    shutil.copy2(DATABASE_PATH, destination)
    with connexion_db() as connexion:
        connexion.execute(
            "INSERT INTO backups_log(filename, created_at, commentaire) VALUES (?, ?, ?)",
            (destination.name, maintenant(), commentaire),
        )
    return destination


def lister_sauvegardes() -> list[Path]:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(BACKUPS_DIR.glob("budget_*.db"), reverse=True)


def restaurer_sauvegarde(nom_fichier: str) -> None:
    source = (BACKUPS_DIR / nom_fichier).resolve()
    if source.parent != BACKUPS_DIR.resolve() or not source.exists():
        raise FileNotFoundError("Sauvegarde introuvable.")
    creer_sauvegarde("Sauvegarde automatique avant restauration")
    copie_temporaire = DATABASE_PATH.with_suffix(".restauration.tmp")
    shutil.copy2(source, copie_temporaire)
    copie_temporaire.replace(DATABASE_PATH)


def exporter_transactions_csv() -> Path:
    import pandas as pd

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = EXPORTS_DIR / f"transactions_{datetime.now():%Y%m%d_%H%M%S}.csv"
    pd.DataFrame(lister_transactions()).to_csv(
        destination, index=False, sep=";", encoding="utf-8-sig", decimal=","
    )
    return destination

