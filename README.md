# Budget_app

Application web locale de suivi de budget personnel, conçue pour remplacer un suivi Excel sans cloud, sans VBA et sans transmission de données personnelles.

## Fonctionnalités V1.5

- tableau de bord avec KPI, graphiques, alertes et comparaison au mois précédent ;
- saisie, filtrage et suppression confirmée des transactions ;
- modification rapide et sauvegardée des transactions existantes ;
- import bancaire manuel CSV/XLSX avec association des colonnes et relecture ;
- règles d’affectation automatiques, détection des doublons et validation sélective ;
- budget mensuel éditable et duplication du mois précédent ;
- suivi chronologique de l’épargne ;
- catégories dynamiques activables et désactivables ;
- thèmes clairs et sombres ;
- sauvegarde/restauration SQLite et export CSV.

La connexion bancaire automatique, OFX/QIF/CMI et la section « Courses et recettes » ne font pas partie de cette version.

## Import bancaire

La page **Import bancaire** accepte les CSV séparés par point-virgule, virgule ou tabulation, ainsi que les fichiers Excel `.xlsx`. Après l’aperçu, associez Date réelle, Libellé et Montant — ou Débit/Crédit — puis relisez chaque proposition avant validation. Les doublons probables sont visibles mais décochés. Une sauvegarde SQLite est créée automatiquement avant toute insertion.

Les mots-clés et priorités se gèrent dans **Paramètres > Règles d’affectation bancaire**. La règle WERO demande toujours une relecture : complétez son sens et la catégorie remboursée avant de l’importer.

## Installation et lancement sous Windows

1. Installer Python 3.11 ou 3.12 depuis python.org en cochant l’ajout de Python au `PATH`.
2. Double-cliquer sur `start_app.bat`.
3. Au premier lancement, patienter pendant la création de `.venv` et l’installation des dépendances.
4. Le navigateur s’ouvre sur l’application. Pour l’arrêter, fermer la fenêtre de commande ou utiliser `Ctrl+C`.

Le lanceur tente d’abord `py`, puis `python`. Il laisse la fenêtre ouverte et affiche un message explicite en cas d’erreur.

## Lancement manuel

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Données locales et GitHub

La base est créée automatiquement dans `data/budget.db`. Les sauvegardes vont dans `backups/` et les exports dans `exports/`. Ces fichiers sont exclus par `.gitignore` : ils ne doivent jamais être ajoutés à GitHub. Seuls les fichiers `.gitkeep` conservent les dossiers vides dans le dépôt.

Voir aussi [le mode d’emploi](docs/mode_emploi.md), [l’architecture](docs/architecture.md) et [le cahier des charges](docs/cahier_des_charges.md).
