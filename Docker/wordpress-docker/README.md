# Wordpress Dockerisé sécurisé

## Description

Déploiement d’une application Wordpress avec une base MySQL sécurisée via Docker Compose et Docker Secrets.

## Structure du projet

wordpress-docker/
├── docker-compose.yml
├── .env
├── secrets/
│ ├── mysql_root_password
│ └── mysql_password
├── README.md


## Variables d’environnement

| Variable | Rôle |
| -------- | ---- |
| MYSQL_DATABASE | Nom de la base Wordpress |
| MYSQL_USER | Utilisateur MySQL |
| WORDPRESS_DB_NAME | Nom de la base utilisée par Wordpress |
| WORDPRESS_DB_USER | Utilisateur utilisé par Wordpress |
| WORDPRESS_DB_HOST | Adresse de la base MySQL |

Les mots de passe sont gérés via **Docker Secrets**.

## Lancer l’application

docker compose up -d
Accès : http://localhost