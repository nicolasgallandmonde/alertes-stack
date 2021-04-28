# Installation
## Dossiers
Créer un dossier pour l'environnement que vous voulez créer.  
Y mettre ce projet ainsi que le projet "lemonde-alertes".    
Un dossier "persistance" sera également automatiquement crée.  

## .env
Créer un fichier .env à la racine avec ces variables initialisées :  
- DAGSTER_HOST_PORT : host et port de dagster
- COMPOSE_PROJECT_NAME : configure le nom du projet pour docker compose. Permet de faire cohabiter plusieurs environnements
- CONF_DIRECTORY : dossier qui contient les toml de configuation des exports / alerets
  
exemple :   
  
DAGSTER_HOST_PORT=127.0.0.1:3005  
COMPOSE_PROJECT_NAME=PROD  
CONF_DIRECTORY=../alerts-conf 



## créer l fichier de credentials
Copier le fichier credentials_template.json en .credentials.json et remplir les credentials n�cessaires

# Lancer et arrêter le projet
Pour lancer le projet : docker-compose up -d  
Pour �teindre : docker-compose down  
Pour entrer en bash dans un conteneur, executer bash.sh  
  
En cas de redémarrage du conteneur dagster il y a quelques étapes à suivre :   
1. réactiver les scheduling dans l'UI de dagster (tant que la bdd dagster n'est pas persistée).  
  
2. pour pouvoir accéder au conteneur par ssh directement sans passer par l'hôte (pour accéder en remote avec vscode par exemple)
echo "root:choisir_un_password"|chpasswd  
service ssh restart  
  
3. pour permettre à dagster de faire des git pull sur le projet qui contient les confs
ssh-keygen   
ajouter dans le repo git la clé publique qui se trouve dans /root/.ssh/id_rsa.pub  
faire un premier git pull à la main dans un terminal pour ajouter l'host aux hotes connus  
