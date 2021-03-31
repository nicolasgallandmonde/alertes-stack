# Installation
## Dossiers
Créer un dossier pour l'environnement que vous voulez créer.  
Y mettre ce projet ainsi que le projet "lemonde-alertes".    
Un dossier "persistance" sera également automatiquement crée.  

## .env
Créer un fichier .env à la racine avec ces variables initialisées :  
DAGSTER_PORT=3005  
METABASE_PORT=3013  
COMPOSE_PROJECT_NAME=PROD  

## créer les fichiers de credentials
Créer un dossier "credentials" dans le dossier "code", et y créer les 4 fichiers suivants :
- un fichier "AT" : qui contient les credentials AT au format "email:password"
- un fichier "amplitude" : qui contient les credentials de l'API amplitude au format "user:password"
- un fichier "google_sheets" : qui contient les credentials google sheets au format JSON
- un fichier "slack" : qui contient la clé de bot slack "xoxb-......"

# Lancer et arrêter le projet
Executer le script up.sh ou down.sh pour lancer et arreter les conteneurs.  
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
