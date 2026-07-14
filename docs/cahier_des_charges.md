# Cahier des charges — V1

## Objectif

Fournir une application locale en français pour suivre les revenus, dépenses, remboursements, budgets et l’épargne d’un compte courant. L’application fonctionne avec Streamlit, SQLite, Pandas et Plotly et se lance sous Windows avec `start_app.bat`.

## Périmètre fonctionnel

- accueil présentant le module budget actif et le futur module courses ;
- transactions manuelles, filtres, recherche, totaux et suppression confirmée ;
- catégories dynamiques avec ajout, modification, désactivation et suppression protégée ;
- création du premier budget, modification des montants et duplication du mois suivant ;
- calculs mensuels de réel, écart, utilisation et statut ;
- suivi d’épargne avec soldes chaînés ;
- tableau de bord avec six KPI et cinq visualisations ;
- paramètres, dix thèmes, sauvegarde, restauration et export CSV.

## Règles essentielles

Les mois sont stockés sous la forme stable `AAAA-MM` et affichés en français (`janv-26`, `févr-26`, etc.). Un revenu dont la catégorie ou le libellé évoque un salaire, une paie ou une paye et daté à partir du 18 est budgété sur le mois suivant. Le mois proposé reste modifiable.

Une dépense possède un montant bancaire négatif mais un montant budgétaire positif. Les remboursements reçus réduisent le réel de la catégorie remboursée ; les remboursements versés l’augmentent. Les versements vers l’épargne augmentent l’épargne réelle et les retraits la diminuent.

## Hors périmètre V1

Import CIC, règles bancaires automatiques, courses et recettes, cloud, mobile, authentification et reprise de l’ancien fichier Excel.

