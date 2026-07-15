# Architecture

## Structure

- `app.py` initialise SQLite, applique le thème et route la navigation ; `navigation.py` conserve explicitement la page active avant chaque relance ;
- `src/database.py` centralise connexions, transactions SQL et paramètres ;
- `src/models/schema.sql` définit les tables et index ;
- `src/services/` contient les règles métier et les calculs ;
- `src/pages/` contient uniquement les vues Streamlit ;
- `src/utils.py` gère les mois français, décalages et formats ;
- `src/themes.py` contient les palettes et le CSS ;
- `src/ui_styles.py` fournit les cartes KPI et le style Plotly partagé ;
- `data/`, `backups/` et `exports/` contiennent les données locales non versionnées.

## Services

- `transactions_service` normalise les signes, calcule le mois budget et gère les transactions ;
- `import_bancaire_service` lit CSV/XLSX, mappe les colonnes, prépare, dédoublonne et valide les lots ;
- `regles_affectation_service` normalise les libellés et applique les règles ordonnées par priorité ;
- `budget_service` crée, duplique et calcule les budgets ;
- `epargne_service` calcule les soldes mensuels chaînés ;
- `tableau_de_bord_service` produit KPI et séries graphiques ;
- `tableau_de_bord_service` génère aussi alertes structurées, comparatif M-1 et résumé par règles ;
- `categories_service` garantit les catégories dynamiques et protège leur suppression ;
- `backup_service` copie/restaure SQLite et exporte le CSV.

## SQLite

`categories` contient les référentiels actifs ou archivés. `transactions` distingue date réelle, mois réel, mois budget, montant bancaire et montant analytique ; `libelle` contient la version lisible et `libelle_bancaire_brut` préserve le texte source. `source`, `statut_import` et `import_id` assurent la traçabilité bancaire. `budgets` contient uniquement les prévisions par mois/type/catégorie. `settings` stocke notamment le thème et la configuration d’affichage sous forme clé/valeur. `backups_log` journalise les sauvegardes. `regles_affectation` stocke mots-clés, affectations, activation et priorité.

Les mois sont stockés en `AAAA-MM` afin que le tri alphabétique soit aussi chronologique. Les dates utilisent le format ISO. Les indicateurs calculés ne sont pas stockés.

## Calculs principaux

Le réel d’une dépense additionne les transactions de dépense et les remboursements rattachés à cette catégorie. L’écart d’une dépense est `prévu - réel`; pour un revenu ou l’épargne, il est `réel - prévu`. Les seuils de vigilance et d’alerte viennent des paramètres. Le solde d’épargne est recalculé dans l’ordre des mois à partir du solde initial.

À l’import, le libellé brut est préservé et une version courte en majuscules est construite en retirant identifiants techniques, numéros de carte, dates et villes courantes. La première règle active par priorité puis identifiant est appliquée. Les doublons utilisent la clé date réelle + montant bancaire arrondi + libellé normalisé. La validation prépare toutes les lignes, crée une sauvegarde, puis insère le lot dans une transaction SQLite.

## Présentation V2

Les six thèmes sombres exposent dix-sept couleurs sémantiques : fonds, cartes, blocs, boutons, textes, bordures, états et trois séries graphiques. `app.py` charge le thème et la configuration d’affichage enregistrés avant le routage ; toutes les pages héritent donc du même CSS. `ui_styles.py` centralise les hauteurs 15/27 pouces des graphiques et tableaux.

Le header natif Streamlit est masqué globalement. `navigation.py` rend donc un contrôle latéral autonome : son état ouvert/fermé est conservé dans `st.session_state`, et une poignée fixe reste disponible quand la sidebar est masquée.

Le comparatif, les alertes et la comparaison budget/réel du Tableau de bord sont rendus en HTML/CSS compact. Plotly reste réservé au graphique principal interchangeable ; la grille inférieure utilise quatre colonnes en configuration 27 pouces et trois en configuration 15 pouces, avec repli responsive.

Le résumé automatique ne fait aucun appel réseau : il combine KPI, alertes et évolution M-1 selon des règles déterministes. La courbe réelle du suivi mensuel contient des valeurs nulles après le dernier jour de dépense, ce qui empêche Plotly de la prolonger artificiellement.

L’éditeur du budget valide le lot complet puis met chaque identifiant à jour dans une transaction SQLite unique. Le mois courant et la version de l’éditeur sont conservés séparément afin qu’un rechargement ne restaure pas un ancien état visuel.
