# Budget_app

Application web locale de suivi de budget personnel, conçue pour remplacer un suivi Excel sans cloud, sans VBA et sans transmission de données personnelles.

## Fonctionnalités V2

- tableau de bord avec KPI, graphiques, alertes et comparaison au mois précédent ;
- résumé mensuel automatique, trajectoire du budget et comparaison détaillée M-1 ;
- saisie en fenêtre compacte, filtrage et suppression multiple confirmée des transactions ;
- modification rapide et sauvegardée des transactions existantes ;
- import bancaire manuel CSV/XLSX avec association des colonnes et relecture ;
- règles d’affectation automatiques, détection des doublons et validation sélective ;
- budget mensuel éditable, duplication et suppression sécurisée d’un mois ;
- suivi chronologique de l’épargne ;
- catégories dynamiques activables et désactivables ;
- six thèmes sombres et deux configurations d’affichage (15 ou 27 pouces) ;
- sauvegarde/restauration SQLite et export CSV.

La connexion bancaire automatique, OFX/QIF/CMI et la section « Courses et recettes » ne font pas partie de cette version.

## Import bancaire

La page **Import bancaire** accepte les CSV séparés par point-virgule, virgule ou tabulation, ainsi que les fichiers Excel `.xlsx`. Après l’aperçu, associez Date réelle, Libellé et Montant — ou Débit/Crédit — puis relisez chaque proposition avant validation. Les doublons probables sont visibles mais décochés. Une sauvegarde SQLite est créée automatiquement avant toute insertion.

Les libellés bancaires techniques sont automatiquement raccourcis pour la lecture, tandis que le libellé brut est conservé en base et visible pendant la relecture. Les mots-clés et priorités se gèrent dans **Paramètres > Règles d’affectation bancaire**. La règle WERO demande toujours une relecture : complétez son sens et la catégorie remboursée avant de l’importer.

## Tableau de bord et thèmes

Le Tableau de bord présente six KPI, quatre graphiques interchangeables, les alertes budget, le comparatif M-1 et un résumé automatique fondé uniquement sur les données locales. Le graphique final compare séparément budget et dépenses par catégorie ; les dépassements y sont mis en évidence.

Six thèmes sombres sont disponibles dans **Paramètres > Apparence**. Le thème par défaut est **Sombre bleu**. Le même écran permet de choisir **Écran 15 pouces** pour une vue très compacte ou **Écran 27 pouces** pour agrandir graphiques et tableaux.

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
