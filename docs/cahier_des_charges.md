# Cahier des charges — V2

## Objectif

Fournir une application locale en français pour suivre les revenus, dépenses, remboursements, budgets et l’épargne d’un compte courant. L’application fonctionne avec Streamlit, SQLite, Pandas et Plotly et se lance sous Windows avec `start_app.bat`.

## Périmètre fonctionnel

- accueil présentant le module budget actif et le futur module courses ;
- transactions manuelles en dialogue, filtres, recherche, totaux et suppression multiple confirmée ;
- modification en tableau des transactions avec sauvegarde préalable ;
- import manuel CSV/XLSX, association des colonnes, relecture et sélection des lignes ;
- règles d’affectation configurables avec priorité et catégories dynamiques ;
- détection conservatrice des doublons sur date, montant et libellé normalisé ;
- catégories dynamiques avec ajout, modification, désactivation et suppression protégée ;
- création du premier budget, modification, duplication et suppression sécurisée d’un mois ;
- calculs mensuels de réel, écart, utilisation et statut ;
- suivi d’épargne avec soldes chaînés ;
- tableau de bord avec six KPI et cinq visualisations ;
- cinq graphiques interchangeables utilisant le thème actif, dont le solde d’épargne ;
- grille compacte budget prévu/réel par catégorie, avec barres horizontales et dépassements visibles ;
- alertes détaillées, comparatif complet M-1 et résumé automatique local ;
- six thèmes sombres complets et configurations compactes pour écrans 15 ou 27 pouces ;
- suivi d’épargne enrichi de cartes mensuelles et d’une courbe de solde ;
- paramètres, sauvegarde, restauration et export CSV.
- navigation persistante après ajout, modification, import ou suppression ;
- menu latéral refermable et réouvrable par une poignée propre à l’application ;
- page Épargne centrée sur le tableau mensuel, les analyses graphiques étant regroupées dans le Tableau de bord.

## Règles essentielles

Les mois sont stockés sous la forme stable `AAAA-MM` et affichés en français (`janv-26`, `févr-26`, etc.). Un revenu dont la catégorie ou le libellé évoque un salaire, une paie ou une paye et daté à partir du 18 est budgété sur le mois suivant. Le mois proposé reste modifiable.

Une dépense possède un montant bancaire négatif mais un montant budgétaire positif. Les remboursements reçus réduisent le réel de la catégorie remboursée ; les remboursements versés l’augmentent. Les versements vers l’épargne augmentent l’épargne réelle et les retraits la diminuent.

## Hors périmètre V1

Connexion bancaire automatique, OFX, QIF, CMI, OCR, courses et recettes, cloud, mobile, authentification et reprise de l’ancien fichier Excel.
