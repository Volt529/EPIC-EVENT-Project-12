Epic Events CRM
Logiciel CRM interne pour Epic Events - gestion des clients, contrats et evenements en ligne de commande.
Prerequis

Python 3.9+
pip

Installation

Cloner le repository


cd epic-events-crm

Creer et activer un environnement virtuel

bashpython -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

Installer les dependances

bashpip install -r requirements.txt

Configurer les variables d'environnement

Renommer _env en .env et renseigner votre DSN Sentry :
SENTRY_DSN=https://votre_dsn@sentry.io/xxxxx

Creer la base de donnees

bashpython test_db.py

Creer le premier administrateur

bashpython create_admin.py
Lancement
bashpython main.py
Roles et permissions
Gestion

Creer, modifier et supprimer des collaborateurs
Creer et modifier tous les contrats
Attribuer un support a un evenement
Supprimer des clients, contrats et evenements

Commercial

Creer et modifier ses propres clients
Creer et modifier les contrats de ses clients
Creer des evenements sur contrats signes
Filtrer les contrats non signes / non payes

Support

Consulter tous les clients, contrats et evenements
Modifier les evenements dont il est responsable
Filtrer ses propres evenements

Commandes disponibles
CommandeDescriptionRoleslist-usersVoir tous les collaborateursTouscreate-userCreer un collaborateurGestionupdate-userModifier un collaborateurGestiondelete-userSupprimer un collaborateurGestionlist-clientsVoir les clientsTouscreate-clientCreer un clientGestion, Com.update-clientModifier un clientGestion, Com.delete-clientSupprimer un clientGestion, Com.list-contractsVoir les contratsTouscreate-contractCreer un contratGestion, Com.update-contractModifier un contratGestion, Com.delete-contractSupprimer un contratGestionlist-unsigned-contractsContrats non signesTouslist-unpaid-contractsContrats non entierement payesTouslist-eventsVoir les evenementsTouscreate-eventCreer un evenementCommercialupdate-eventModifier un evenementGestion, Sup.delete-eventSupprimer un evenementGestionlist-events-without-supportEvenements sans support attribueToushelpAfficher le menu d'aideTousquitQuitter l'applicationTous
Structure du projet
epic-events-crm/
|-- app/
|   |-- __init__.py
|   |-- models.py        # Modeles SQLAlchemy
|   |-- database.py      # Configuration SQLite
|   |-- auth.py          # Authentification bcrypt
|   |-- crud.py          # Operations CRUD
|   |-- cli.py           # Interface Click
|   `-- sentry_config.py # Journalisation Sentry
|-- main.py              # Point d'entree
|-- create_admin.py      # Creation du premier admin
|-- test_db.py           # Initialisation de la BDD
|-- requirements.txt
|-- .env                 # Variables d'environnement (non versionne)
`-- README.md
Schema de la base de donnees
users --< clients --< contracts --< events
  |                      |
  `-- (sales_contact) ---'
  `-- (support_contact) -------> events
Suppressions en cascade activees : supprimer un client supprime ses contrats et evenements.
Securite

Mots de passe haches avec bcrypt
Injections SQL impossibles via SQLAlchemy ORM
Principe du moindre privilege sur toutes les operations
Journalisation des erreurs via Sentry

Technologies
TechnologieUsagePython 3.9+Langage principalSQLAlchemy 2.0ORM et base de donneesSQLiteBase de donneesClick 8Interface ligne de commandebcryptHachage des mots de passeSentry SDKJournalisation des erreurspython-dotenvVariables d'environnement
