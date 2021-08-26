# Alertes slack automatiques basées sur Amplitude et AT

Ce projet permet de tester puis scheduler des alertes slack à partir des données AT et Amplitude

## Comment ça marche
Les alertes sont définies en python dans des notebooks jupyter qui sont ensuite schedulés grace à Dagster, un outil d'orchestration similaire à Airflow.
Les autres outils utilisés sont :
- Dagyter, un projet pour faciliter le scheduling des notebooks Jupyter par Dagster au moyen d'un simple fichier .toml
- Cross-app-menu, un projet qui permet d'afficher plusieurs apps dans une seule page grâce à des iframes et un menu qui s'affiche à droite. En l'occurence, il permet d'afficher Dagster et Jupyter dans la même page

## Getting started
- Créer un fichier urls.conf sur le modèle de url.conf.template. Ce fichier permet de configurer le menu de droite avec les liens et les icones
- Copier le dossier alertes-conf-template en alertes-conf.
- Remplir les credentials (AT, Amplitude, Slack ...) dans le fichier .credentials de ce dossiers
- Lancer les conteneurs ("  docker-compose up -d   ")
Maintenant vous pouvez écrire et tester vos alertes dans jupyter

## Définir les alertes
Voir les notebooks exemple fournis dans le dossier alertes-conf-template.
Quelques indications :
- le chart_id amplitude correspond au chart id qui est présent dans l'url des graphiques amplitude ENREGISTRES (l'API d'amplitude renvoie une erreur si on demande un id de graphique non sauvegardé)
- ... TODO ...

## Scheduler les alertes
Le scheduling des alertes se fait avec l'outil Dagster, qui est un orchestrateur de tâches python.
Pour simplifier le mariage Dagster-Jupyter, j'ai utilisé un de mes projets open-source Dagyter. Il permet de scheduler les notebooks en configurant un simple fichier toml : pipelines_and_scheduling.toml.
La syntaxe est décrite dans le github du projet Dagyter : https://github.com/nicolasgallandpro/dagyter. Sinon l'exemple fourni devrait couvrir la majorité des cas.


