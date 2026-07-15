PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    actif INTEGER NOT NULL DEFAULT 1,
    ordre INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(type, categorie)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_reelle TEXT NOT NULL,
    mois_reel TEXT NOT NULL,
    mois_budget TEXT NOT NULL,
    type TEXT NOT NULL,
    sens_remboursement TEXT,
    categorie TEXT,
    categorie_remboursee TEXT,
    libelle TEXT NOT NULL,
    libelle_bancaire_brut TEXT,
    montant_bancaire REAL NOT NULL,
    montant_budget REAL NOT NULL,
    moyen_paiement TEXT,
    commentaire TEXT,
    source TEXT DEFAULT 'manuel',
    statut_import TEXT,
    import_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mois TEXT NOT NULL,
    type TEXT NOT NULL,
    categorie TEXT NOT NULL,
    budget_prevu REAL NOT NULL DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(mois, type, categorie)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS backups_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    created_at TEXT,
    commentaire TEXT
);

CREATE TABLE IF NOT EXISTS regles_affectation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mot_cle TEXT NOT NULL,
    type_attribue TEXT NOT NULL,
    categorie_attribuee TEXT,
    sens_remboursement TEXT,
    categorie_remboursee TEXT,
    actif INTEGER NOT NULL DEFAULT 1,
    priorite INTEGER DEFAULT 100,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_transactions_mois_budget
    ON transactions(mois_budget);
CREATE INDEX IF NOT EXISTS idx_budgets_mois
    ON budgets(mois);
CREATE INDEX IF NOT EXISTS idx_regles_priorite
    ON regles_affectation(actif, priorite);
