# Mode d’emploi

## Choisir l’apparence

Ouvrez **Paramètres > Apparence**, choisissez l’un des onze thèmes pastel ou sombres, puis enregistrez. Le choix est conservé dans SQLite et s’applique à toutes les pages, y compris les graphiques.

## Lire le Tableau de bord

Sélectionnez un mois budget en haut de **Tableau de bord**. Les six cartes indiquent revenus, budget de dépenses, dépenses réelles, reste disponible, épargne nette et taux d’épargne.

La zone centrale n’affiche qu’un graphique à la fois :

- **Suivi du mois** compare les dépenses cumulées à une consommation théorique régulière du budget ;
- **Dépenses par mois** montre la tendance chronologique ;
- **Équilibre mensuel** compare revenus, dépenses et épargne nette ;
- **Taux d’épargne** suit le pourcentage épargné.

Le bloc **Comparatif M-1** détaille les valeurs du mois, celles du mois précédent, les écarts et évolutions. **Alertes budget** signale dépassements, seuils de vigilance, dépenses sans budget et reste négatif. **Résumé du mois** assemble quelques constats automatiques sans utiliser de service externe.

En bas, le graphique par catégorie exclut les lignes entièrement vides et colore les dépenses dépassant le budget.

## Lancer l’application

Installez Python 3.11 ou 3.12, puis double-cliquez sur `start_app.bat`. Le premier lancement crée l’environnement `.venv`, installe les dépendances et démarre Streamlit. Les lancements suivants réutilisent cet environnement.

## Créer le premier budget

Ouvrez **Budget mensuel**, choisissez l’année et le mois dans la vue annuelle simplifiée, puis cliquez sur **Créer le premier budget**. Une ligne à 0 € est créée pour chaque catégorie active de revenu, dépense et épargne. Modifiez la colonne **Budget prévu**, puis enregistrez. Le bouton **Créer le mois suivant** recopie les montants du dernier mois.

En V2, le tableau est protégé en lecture par défaut. Cliquez sur **Modifier les budgets** pour activer l’édition ; les statuts OK, Vigilance et Dépassement restent visibles et utilisent les seuils définis dans Paramètres.

## Ajouter une transaction

Ouvrez **Transactions** puis **Ajouter une transaction**. Choisissez le type avant de remplir le formulaire : la liste de catégories se met à jour depuis la base locale. Saisissez toujours un montant positif ; l’application applique elle-même le bon signe bancaire et budgétaire.

Pour un remboursement, indiquez le sens et la catégorie de dépense concernée. Pour un salaire daté à partir du 18, le mode **Automatique** propose le mois suivant.

## Importer un fichier bancaire CSV ou Excel

1. Ouvrez **Import bancaire** et sélectionnez un fichier `.csv` ou `.xlsx`.
2. Contrôlez l’aperçu et associez les colonnes **Date réelle**, **Libellé** et **Montant**. Si la banque sépare les flux, choisissez **Deux colonnes Débit et Crédit**.
3. Cliquez sur **Préparer les transactions**. L’application normalise dates et montants, applique les règles et recherche les doublons.
4. Dans la table de relecture, modifiez librement les types, catégories, mois, montants et commentaires. Cochez uniquement les lignes souhaitées.
5. Cliquez sur **Valider l’import**. Une sauvegarde automatique précède l’insertion et le nombre de transactions ajoutées est affiché.

Les CSV courants UTF-8 ou latin1, séparés par point-virgule, virgule ou tabulation, sont reconnus. Un message en français précise les fichiers ou lignes illisibles.

### Règles d’affectation et WERO

Les règles sont insensibles à la casse et aux accents. Si plusieurs mots-clés correspondent, la priorité numérique la plus faible gagne : CARREFOUR (10) est donc évalué avant CARRE (20). Ajoutez, modifiez, désactivez ou supprimez les règles dans **Paramètres > Règles d’affectation bancaire**.

WERO est proposé comme **Remboursement** avec le statut **À vérifier**. Avant validation, choisissez **On me rembourse** ou **Je rembourse quelqu’un**, puis la catégorie remboursée. Une ligne incomplète ne peut pas être insérée.

### Doublons probables

Une ligne est signalée si une transaction existante possède la même date, le même montant bancaire et le même libellé normalisé. Elle reste visible mais **Importer** est décoché. Vous pouvez la recocher si le mouvement est réellement distinct.

## Modifier rapidement des transactions

Dans **Transactions**, appliquez éventuellement des filtres puis cliquez sur **Activer la modification**. Modifiez les cellules souhaitées et cliquez sur **Enregistrer les modifications**. Seules les lignes filtrées sont présentées et une sauvegarde automatique est créée avant l’écriture.

## Modifier le mois budget

Dans le formulaire, utilisez **M-2**, **M-1**, **M**, **M+1** ou **M+2** par rapport à la date réelle. **Autre** permet de choisir séparément l’année et le mois : il s’agit de la vue annuelle simplifiée de la V1.

## Gérer les catégories

La page **Catégories** permet d’ajouter, renommer, ordonner ou désactiver une catégorie. Une nouvelle catégorie active apparaît immédiatement dans les transactions et reçoit une ligne à 0 € dans tous les mois budgétaires existants. Une catégorie déjà utilisée n’est jamais supprimée : elle est désactivée.

## Sauvegarder, restaurer et exporter

Dans **Paramètres**, créez une sauvegarde manuelle avant une modification importante. Lors d’une restauration, l’application crée aussi automatiquement une copie de sécurité de la base actuelle. L’export CSV est écrit dans `exports/` au format français (séparateur point-virgule, décimale virgule).

## Utiliser GitHub sans publier ses données

Ne forcez jamais l’ajout des dossiers `data/`, `backups/` ou `exports/`. Le `.gitignore` protège la base SQLite et les fichiers personnels, tandis que les `.gitkeep` maintiennent les dossiers dans le dépôt. Avant un envoi, vérifiez avec `git status` qu’aucun fichier `.db`, `.sqlite`, de sauvegarde ou d’export CSV n’est suivi.
