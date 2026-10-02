# MATHutrice

MATHutrice est un tuteur pédagogique fondé sur un LLM. Il aide les étudiants
de première année de l'EPF à travailler les notions et compétences de
mathématiques, à s'entraîner et à suivre leur progression.

La branche de référence du cours est `course-2026`.

## Lancer le projet localement

### Prérequis

- Python 3.14.7, indiqué dans `.python-version` ;
- [uv](https://docs.astral.sh/uv/) pour installer Python et les dépendances
  verrouillées dans `uv.lock` ;
- une clé pour un endpoint compatible avec l'API OpenAI. La configuration par
  défaut utilise Mistral.

Clonez votre fork et placez-vous sur la branche du cours :

```sh
git clone -b course-2026 <URL-DE-VOTRE-FORK> mathutrice
cd mathutrice
```

Installez ensuite les dépendances et créez la configuration locale :

```sh
uv sync
cp .env.example .env
```

Renseignez au minimum `LLM_API_KEY` dans `.env`, puis démarrez l'application :

```sh
uv run uvicorn mathutrice.app:app --port 8000
```

Ouvrez ensuite <http://localhost:8000/>. Au premier démarrage d'une base vide,
l'application crée les notions, les compétences et un utilisateur de
développement pour chacun des rôles Student, Teacher et Admin.

Le protocole complet permettant de vérifier qu'un clone neuf fonctionne est
décrit dans [docs/smoke-test.md](docs/smoke-test.md).

## Configuration

`.env.example` contient toutes les variables lues par l'application :

| Variable | Utilisation |
| --- | --- |
| `AUTH_MODE` | `entra` par défaut si la variable est absente ; utilisez `dev` uniquement en développement local. |
| `DEV_LOGIN_KEY` | Clé partagée facultative qui protège la page de connexion de développement. Ignorée en mode `entra`. |
| `SESSION_SECRET` | Clé de signature des cookies de session. Elle est obligatoire. |
| `DATABASE_URL` | URL SQLAlchemy de la base. L'exemple utilise un fichier SQLite local. |
| `LLM_BASE_URL` | URL de l'endpoint LLM compatible avec l'API OpenAI. |
| `LLM_MODEL` | Nom du modèle servi par cet endpoint. |
| `LLM_API_KEY` | Clé de l'endpoint LLM. Elle est obligatoire. |
| `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID` | Identifiants Microsoft Entra ID, obligatoires en mode `entra`. |
| `REDIRECT_URL` | URL de retour OAuth, obligatoire en mode `entra`. |
| `POST_LOGOUT_REDIRECT_URL` | URL de retour après déconnexion, obligatoire en mode `entra`. |

Ne commitez jamais `.env` ni une clé. Le fichier est ignoré par Git.

## Connexion de développement

Avec `AUTH_MODE=dev`, `/dev/login` permet de choisir une adresse EPF et un rôle
sans aucune preuve d'identité. Cette connexion de développement ne doit jamais
être activée en production.

`DEV_LOGIN_KEY` peut protéger le formulaire avec une clé partagée, mais ne
remplace pas une authentification. De plus, la valeur d'exemple de
`SESSION_SECRET` n'est pas sûre : une personne qui la connaît peut fabriquer un
cookie de session et contourner `DEV_LOGIN_KEY`. Remplacez toujours cette
valeur par un secret aléatoire hors du poste local.

Une connexion scriptée peut conserver le cookie dans un fichier :

```sh
curl -i -c cookies.txt \
  -d 'email=student@epfedu.fr' \
  -d 'role=student' \
  -d 'key=la-valeur-de-DEV_LOGIN_KEY' \
  http://localhost:8000/dev/login

curl -b cookies.txt http://localhost:8000/
```

Supprimez l'option `key` lorsque `DEV_LOGIN_KEY` est vide. Le fichier
`cookies.txt` contient une session active : ne le commitez pas et supprimez-le
après le test.

## Déploiement

Avant tout déploiement, vérifiez au minimum :

- `AUTH_MODE` non défini ou `entra` ;
- les cinq variables Entra correctement définies ;
- `SESSION_SECRET` remplacé par une valeur aléatoire et confidentielle ;
- `DEV_LOGIN_KEY` absent ;
- `DATABASE_URL` pointant vers la base de production ;
- les paramètres et la clé de l'endpoint LLM stockés comme secrets ;
- aucune valeur de `.env` ni aucun fichier de cookies suivi par Git.

## Architecture

Le code Python importable se trouve sous `mathutrice/`. Les conventions de
paquets et les commandes de contrôle sont documentées dans
[mathutrice/README.md](mathutrice/README.md). Les décisions d'architecture sont
conservées dans [docs/adr/](docs/adr/).
