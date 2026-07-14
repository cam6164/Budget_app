from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
EXPORTS_DIR = BASE_DIR / "exports"
DATABASE_PATH = DATA_DIR / "budget.db"
SCHEMA_PATH = BASE_DIR / "src" / "models" / "schema.sql"

TYPES_TRANSACTION = ["Revenu", "Dépense", "Épargne", "Remboursement"]
TYPES_BUDGET = ["Revenu", "Dépense", "Épargne"]
SENS_REMBOURSEMENT = ["On me rembourse", "Je rembourse quelqu’un"]
MOYENS_PAIEMENT = ["Virement", "CB", "Espèces", "Tickets Resto", "Autre"]

PARAMETRES_DEFAUT = {
    "theme_actif": "Vert pastel",
    "solde_initial_epargne": "0",
    "seuil_vigilance_budget": "0.8",
    "seuil_alerte_budget": "1.0",
}

CATEGORIES_DEFAUT = {
    "Revenu": ["Salaire", "CAF", "Prime", "Autre revenu"],
    "Dépense": [
        "Courses", "Transport", "Bar", "Restaurant", "Sport", "Logement",
        "Abonnements", "Santé", "Loisirs", "Autre dépense",
    ],
    "Épargne": ["Virement vers épargne", "Retrait depuis épargne"],
    "Remboursement": ["Remboursement"],
}

