#!/bin/sh

#--- activation du ssh forwarding, à executer à l'intérieur une fois le conteneur lancé :
#read -s passww # marche pas parfois ?
#echo "root:passww"|chpasswd
#service ssh restart

#--- 
dagster-daemon run &
dagit -h "0.0.0.0" -p "3000" -w "/opt/dagster/app/workspace.yaml"
