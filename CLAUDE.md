# Prêt pour GTA 6 : règles de travail

Ce dépôt est un site statique publié par GitHub Pages sur https://yay-tech.github.io/guide-gta6/ (branche `main`, racine).
Propriétaire : Yaya (compte GitHub Yay-tech), étudiant à Bruxelles. Il ne code pas et veut le minimum de travail.

## But du site
Guide d'achat en français pour la Belgique autour de GTA 6 (consoles, accessoires, timing, parents).
Revenus : liens affiliés Amazon Belgique, identifiant `yaya098-21`. Les visites doivent venir de Google, donc chaque page doit être vraiment utile.

## Règles non négociables
- Tout lien Amazon passe par `https://www.amazon.com.be/` et porte `tag=yaya098-21`, avec `rel="sponsored noopener"`.
- Ne jamais afficher un prix comme « prix Amazon ». On affiche seulement les prix conseillés officiels (Sony, Microsoft, Rockstar) et on renvoie vers « Voir le prix du jour ».
- Garder la mention affiliée en haut et en bas de chaque page, avec la phrase exacte : « En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises. »
- Interdit : faux avis, faux témoignages, faux stock limité, faux compte à rebours, contenu copié d'autres sites, pages vides écrites pour Google.
- Chaque fait (prix, date, caractéristique) est vérifié par une recherche le jour même. En cas de doute, on ne l'écrit pas.
- Français simple, phrases courtes, pas de jargon, pas de tirets longs dans le texte.
- Le site doit rester lisible sur téléphone et en mode sombre. Réutiliser le style de `index.html` (mêmes couleurs, mêmes polices intégrées).

## Tâche hebdomadaire (exécutée automatiquement)
1. Vérifier les nouvelles importantes (GTA 6, version PC, prix des consoles en euros, promotions majeures). Corriger `index.html` si un fait a changé, et mettre à jour la date « Mis à jour le ».
2. Ajouter au plus UNE nouvelle page utile par semaine, dans un dossier `/<slug>/index.html`, sur une question que les gens cherchent vraiment. Priorités : GTA 6 sur PC (configuration conseillée, budget), contrôle parental, stockage plein, manette, casque, cadeaux, comparatifs simples.
3. Ajouter un lien vers la nouvelle page depuis `index.html` (section « Guides pratiques ») et l'ajouter à `sitemap.xml`.
4. Tenir un journal court dans `JOURNAL.md` : date, ce qui a changé, sources utilisées.
5. Commit sur `main` avec un message clair en français, puis push.
6. Si une décision coûte de l'argent, touche au compte Amazon ou change la stratégie : ne rien faire et l'écrire en haut de `JOURNAL.md` sous « À valider par Yaya ».
