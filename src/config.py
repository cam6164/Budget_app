import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("BUDGET_APP_DATA_DIR", BASE_DIR / "data"))
BACKUPS_DIR = Path(os.environ.get("BUDGET_APP_BACKUPS_DIR", BASE_DIR / "backups"))
EXPORTS_DIR = Path(os.environ.get("BUDGET_APP_EXPORTS_DIR", BASE_DIR / "exports"))
DATABASE_PATH = Path(os.environ.get("BUDGET_APP_DATABASE_PATH", DATA_DIR / "budget.db"))
SCHEMA_PATH = BASE_DIR / "src" / "models" / "schema.sql"

TYPES_TRANSACTION = ["Revenu", "Dépense", "Épargne", "Remboursement"]
TYPES_BUDGET = ["Revenu", "Dépense", "Épargne"]
SENS_REMBOURSEMENT = ["On me rembourse", "Je rembourse quelqu’un"]
MOYENS_PAIEMENT = ["Virement", "CB", "Espèces", "Tickets Resto", "Autre"]
STATUTS_IMPORT = ["À vérifier", "Validée", "Ignorée", "Doublon probable"]

PARAMETRES_DEFAUT = {
    "theme_actif": "Sombre bleu",
    "configuration_affichage": "ecran_15",
    "solde_initial_epargne": "0",
    "seuil_vigilance_budget": "0.8",
    "seuil_alerte_budget": "1.0",
}

THEMES_AUTORISES = [
    "Sombre bleu",
    "Sombre vert",
    "Sombre orange",
    "Sombre gris",
    "Sombre violet",
    "Sombre doré",
]

CONFIGURATIONS_AFFICHAGE = {
    "Écran 15 pouces": "ecran_15",
    "Écran 27 pouces": "ecran_27",
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

REGLES_AFFECTATION_DEFAUT = [
    {"mot_cle": "CARREFOUR", "type_attribue": "Dépense", "categorie_attribuee": "Courses", "priorite": 10},
    {"mot_cle": "ENGIE", "type_attribue": "Revenu", "categorie_attribuee": "Salaire", "priorite": 10},
    {"mot_cle": "SNCF", "type_attribue": "Dépense", "categorie_attribuee": "Transport", "priorite": 10},
    {"mot_cle": "WERO", "type_attribue": "Remboursement", "categorie_attribuee": "", "sens_remboursement": "", "categorie_remboursee": "", "priorite": 5},
    {"mot_cle": "CARRE", "type_attribue": "Dépense", "categorie_attribuee": "Bar", "priorite": 20},
    {"mot_cle": "COCCI", "type_attribue": "Dépense", "categorie_attribuee": "Courses", "priorite": 10},
    {"mot_cle": "DECATHLON", "type_attribue": "Dépense", "categorie_attribuee": "Sport", "priorite": 10},
]
