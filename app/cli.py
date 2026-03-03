import click
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import authenticate_user
from app.models import User, Client, Contract, Event
from app.crud import (
    create_collaborator, get_all_users, delete_user, update_collaborator,
    create_client, get_all_clients, get_clients_by_sales, delete_client, update_client,
    create_contract, get_all_contracts, get_unsigned_contracts, get_unpaid_contracts, delete_contract, update_contract,
    create_event, get_all_events, get_events_by_support, get_events_without_support, update_event, delete_event
)
from datetime import datetime


current_user: User | None = None


def set_current_user(user: User):
    global current_user
    current_user = user


def get_current_user() -> User:
    if current_user is None:
        raise click.ClickException("Vous devez d'abord vous connecter.")
    return current_user


def require_role(*allowed_roles: str):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user.role not in allowed_roles:
                raise click.ClickException(f"Accès refusé : rôle requis {', '.join(allowed_roles)}")
            return f(*args, **kwargs)
        return wrapper
    return decorator


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(login)


@cli.command()
def login():
    db: Session = next(get_db())
    username = click.prompt("Nom d'utilisateur")
    password = click.prompt("Mot de passe", hide_input=True)

    user = authenticate_user(db, username, password)
    if user:
        set_current_user(user)
        click.echo(f"\nConnexion réussie ! Bienvenue {user.full_name} ({user.role.upper()})\n")
        interactive_menu()
    else:
        click.echo("\nIdentifiants incorrects.\n")


# ======================
# Commandes (TOUTES définies avant le dictionnaire)
# ======================

def list_users_cmd():
    db: Session = next(get_db())
    users = get_all_users(db)
    click.echo("\n=== Liste des collaborateurs ===")
    if not users:
        click.echo("Aucun collaborateur.")
        return
    for u in users:
        click.echo(f"ID: {u.id} | {u.full_name} | {u.username} | Rôle: {u.role}")


@require_role("gestion")
def delete_user_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    users = get_all_users(db)
    click.echo("\n=== Suppression d'un collaborateur ===")
    for u in users:
        click.echo(f"ID: {u.id} | {u.full_name} | {u.username} | Rôle: {u.role}")
    user_id = click.prompt("ID du collaborateur à supprimer", type=int)
    if click.confirm(f"⚠️  Confirmez la suppression du collaborateur ID {user_id} ? (irréversible)", default=False):
        try:
            delete_user(db, user, user_id)
            click.echo("Collaborateur supprimé avec succès.")
        except Exception as e:
            click.echo(f"Erreur : {e}")


@require_role("gestion")
def update_user_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    users = get_all_users(db)
    click.echo("\n=== Modification d'un collaborateur ===")
    for u in users:
        click.echo(f"ID: {u.id} | {u.full_name} | {u.username} | Rôle: {u.role}")
    user_id = click.prompt("ID du collaborateur à modifier", type=int)
    updates = {}
    if click.confirm("Modifier le nom complet ?", default=False):
        updates["full_name"] = click.prompt("Nouveau nom complet")
    if click.confirm("Modifier le nom d'utilisateur ?", default=False):
        updates["username"] = click.prompt("Nouveau nom d'utilisateur")
    if click.confirm("Modifier le rôle ?", default=False):
        updates["role"] = click.prompt("Nouveau rôle", type=click.Choice(["gestion", "commercial", "support"]))
    if click.confirm("Modifier le mot de passe ?", default=False):
        updates["password"] = click.prompt("Nouveau mot de passe", hide_input=True, confirmation_prompt=True)
    if updates:
        try:
            update_collaborator(db, user, user_id, **updates)
            click.echo("\nCollaborateur mis à jour avec succès !")
        except Exception as e:
            click.echo(f"Erreur : {e}")
    else:
        click.echo("Aucune modification apportée.")


def list_clients_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    clients = get_clients_by_sales(db, user.id) if user.role == "commercial" else get_all_clients(db)
    click.echo(f"\n=== {'Vos clients' if user.role == 'commercial' else 'Tous les clients'} ===")
    if not clients:
        click.echo("Aucun client.")
        return
    
    erreur_test = 10 / 0

    for c in clients:
        contact = c.sales_contact.full_name if c.sales_contact else "Aucun"
        click.echo(f"ID: {c.id} | {c.full_name} | {c.email} | {c.company or 'N/A'} | Contact: {contact}")


@require_role("gestion", "commercial")
def create_client_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    click.echo("\nCréation d'un nouveau client (Ctrl+C pour annuler)")
    full_name = click.prompt("Nom complet du client")
    email = click.prompt("Email du client")
    phone = click.prompt("Téléphone (Entrée pour laisser vide)", default="")
    company = click.prompt("Entreprise (Entrée pour laisser vide)", default="")

    try:
        client = create_client(db, user, full_name, email, phone or None, company or None)
        click.echo(f"\nClient créé avec succès ! ID: {client.id}")
    except Exception as e:
        click.echo(f"Erreur : {e}")


@require_role("gestion", "commercial")
def delete_client_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    clients = get_clients_by_sales(db, user.id) if user.role == "commercial" else get_all_clients(db)
    click.echo("\n=== Suppression d'un client ===")
    if not clients:
        click.echo("Aucun client disponible.")
        return
    for c in clients:
        click.echo(f"ID: {c.id} | {c.full_name} | {c.email}")
    client_id = click.prompt("ID du client à supprimer", type=int)
    if click.confirm(f"⚠️  Confirmez la suppression du client ID {client_id} ? (contrats et événements associés seront supprimés)", default=False):
        try:
            delete_client(db, user, client_id)
            click.echo("Client supprimé avec succès.")
        except Exception as e:
            click.echo(f"Erreur : {e}")


@require_role("gestion", "commercial")
def update_client_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    clients = get_clients_by_sales(db, user.id) if user.role == "commercial" else get_all_clients(db)
    click.echo("\n=== Modification d'un client ===")
    if not clients:
        click.echo("Aucun client disponible.")
        return
    for c in clients:
        click.echo(f"ID: {c.id} | {c.full_name} | {c.email} | {c.company or 'N/A'}")
    client_id = click.prompt("ID du client à modifier", type=int)
    updates = {}
    if click.confirm("Modifier le nom complet ?", default=False):
        updates["full_name"] = click.prompt("Nouveau nom complet")
    if click.confirm("Modifier l'email ?", default=False):
        updates["email"] = click.prompt("Nouvel email")
    if click.confirm("Modifier le téléphone ?", default=False):
        updates["phone"] = click.prompt("Nouveau téléphone (Entrée pour vider)", default="")
    if click.confirm("Modifier l'entreprise ?", default=False):
        updates["company"] = click.prompt("Nouvelle entreprise (Entrée pour vider)", default="")
    if user.role == "gestion" and click.confirm("Changer le commercial assigné ?", default=False):
        commerciaux = db.query(User).filter(User.role == "commercial").all()
        for s in commerciaux:
            click.echo(f"  ID {s.id} → {s.full_name}")
        updates["sales_contact_id"] = click.prompt("ID du commercial", type=int)
    if updates:
        try:
            update_client(db, user, client_id, **updates)
            click.echo("\nClient mis à jour avec succès !")
        except Exception as e:
            click.echo(f"Erreur : {e}")
    else:
        click.echo("Aucune modification apportée.")


@require_role("gestion")
def create_user_cmd():
    db: Session = next(get_db())
    click.echo("\nCréation d'un nouveau collaborateur (Ctrl+C pour annuler)")
    username = click.prompt("Nom d'utilisateur")
    password = click.prompt("Mot de passe", hide_input=True, confirmation_prompt=True)
    full_name = click.prompt("Nom complet")
    role = click.prompt("Rôle", type=click.Choice(["gestion", "commercial", "support"]))
    try:
        user = create_collaborator(db, username, password, full_name, role)
        click.echo(f"\nCollaborateur créé avec succès : {user.full_name} ({user.role})")
    except Exception as e:
        click.echo(f"Erreur : {e}")


def list_contracts_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    if user.role == "commercial":
        contracts = db.query(Contract).join(Client).filter(Client.sales_contact_id == user.id).all()
        click.echo(f"\n=== Vos contrats ({user.full_name}) ===")
    else:
        contracts = get_all_contracts(db)
        click.echo("\n=== Tous les contrats ===")
    if not contracts:
        click.echo("Aucun contrat.")
        return
    for c in contracts:
        status = "Signé" if c.is_signed else "Non signé"
        payment = "Payé entièrement" if c.remaining_amount == 0 else f"Reste {c.remaining_amount} €"
        click.echo(f"ID: {c.id} | Client: {c.client.full_name} | Total: {c.total_amount} € | {payment} | Statut: {status}")


def list_unsigned_contracts_cmd():
    db: Session = next(get_db())
    contracts = get_unsigned_contracts(db)
    click.echo("\n=== Contrats non signés ===")
    if not contracts:
        click.echo("Tous les contrats sont signés.")
        return
    for c in contracts:
        click.echo(f"ID: {c.id} | Client: {c.client.full_name} | Total: {c.total_amount} €")


def list_unpaid_contracts_cmd():
    db: Session = next(get_db())
    contracts = get_unpaid_contracts(db)
    click.echo("\n=== Contrats non entièrement payés ===")
    if not contracts:
        click.echo("Tous les contrats sont payés.")
        return
    for c in contracts:
        click.echo(f"ID: {c.id} | Client: {c.client.full_name} | Reste: {c.remaining_amount} €")


@require_role("gestion", "commercial")
def create_contract_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    clients = get_clients_by_sales(db, user.id) if user.role == "commercial" else get_all_clients(db)
    if not clients:
        click.echo("Aucun client disponible.")
        return
    click.echo("\nClients disponibles :")
    for cl in clients:
        click.echo(f"  ID {cl.id} → {cl.full_name} ({cl.company or 'N/A'})")
    client_id = click.prompt("ID du client", type=int)
    total_amount = click.prompt("Montant total (€)", type=float)
    remaining_amount = click.prompt("Montant restant à payer (€) (Entrée pour égal au total)", type=float, default=total_amount)
    is_signed = click.confirm("Le contrat est-il déjà signé ?", default=False)
    try:
        contract = create_contract(db, user, client_id, total_amount, remaining_amount, is_signed)
        click.echo(f"\nContrat créé avec succès ! ID: {contract.id}")
    except Exception as e:
        click.echo(f"Erreur : {e}")


@require_role("gestion")
def delete_contract_cmd():
    db: Session = next(get_db())
    contracts = get_all_contracts(db)
    click.echo("\n=== Suppression d'un contrat ===")
    if not contracts:
        click.echo("Aucun contrat disponible.")
        return
    for c in contracts:
        click.echo(f"ID: {c.id} | Client: {c.client.full_name} | Total: {c.total_amount} €")
    contract_id = click.prompt("ID du contrat à supprimer", type=int)
    if click.confirm(f"⚠️  Confirmez la suppression du contrat ID {contract_id} ? (événements associés seront supprimés)", default=False):
        try:
            delete_contract(db, get_current_user(), contract_id)
            click.echo("Contrat supprimé avec succès.")
        except Exception as e:
            click.echo(f"Erreur : {e}")


@require_role("gestion", "commercial")
def update_contract_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    if user.role == "commercial":
        contracts = db.query(Contract).join(Client).filter(Client.sales_contact_id == user.id).all()
    else:
        contracts = get_all_contracts(db)
    click.echo("\n=== Modification d'un contrat ===")
    if not contracts:
        click.echo("Aucun contrat disponible.")
        return
    for c in contracts:
        status = "Signé" if c.is_signed else "Non signé"
        click.echo(f"ID: {c.id} | Client: {c.client.full_name} | Total: {c.total_amount} € | Reste: {c.remaining_amount} € | {status}")
    contract_id = click.prompt("ID du contrat à modifier", type=int)
    updates = {}
    if click.confirm("Modifier le montant total ?", default=False):
        updates["total_amount"] = click.prompt("Nouveau montant total (€)", type=float)
    if click.confirm("Modifier le montant restant ?", default=False):
        updates["remaining_amount"] = click.prompt("Nouveau montant restant (€)", type=float)
    if click.confirm("Changer le statut de signature ?", default=False):
        updates["is_signed"] = click.confirm("Le contrat est-il signé ?", default=False)
    if updates:
        try:
            update_contract(db, user, contract_id, **updates)
            click.echo("\nContrat mis à jour avec succès !")
        except Exception as e:
            click.echo(f"Erreur : {e}")
    else:
        click.echo("Aucune modification apportée.")


def list_events_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    events = get_events_by_support(db, user.id) if user.role == "support" else get_all_events(db)
    click.echo(f"\n=== {'Vos événements' if user.role == 'support' else 'Tous les événements'} ===")
    if not events:
        click.echo("Aucun événement.")
        return
    for e in events:
        start_fr = e.start_date.strftime("%d/%m/%Y %H:%M")
        end_fr = e.end_date.strftime("%d/%m/%Y %H:%M")
        support = e.support_contact.full_name if e.support_contact else "Non attribué"
        click.echo(f"ID: {e.id} | {e.event_name}")
        click.echo(f"   Du {start_fr} au {end_fr}")
        click.echo(f"   Lieu: {e.location or 'Non spécifié'} | Participants: {e.attendees}")
        click.echo(f"   Support: {support}")
        if e.notes:
            click.echo(f"   Notes: {e.notes}")
        click.echo("")


def list_events_without_support_cmd():
    db: Session = next(get_db())
    events = get_events_without_support(db)
    click.echo("\n=== Événements sans support attribué ===")
    if not events:
        click.echo("Tous les événements ont un support.")
        return
    for e in events:
        start_fr = e.start_date.strftime("%d/%m/%Y %H:%M")
        end_fr = e.end_date.strftime("%d/%m/%Y %H:%M")
        click.echo(f"ID: {e.id} | {e.event_name} | Contrat ID: {e.contract_id}")
        click.echo(f"   Du {start_fr} au {end_fr}")
        click.echo("")


@require_role("commercial")
def create_event_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    signed_contracts = db.query(Contract).join(Client).filter(
        Client.sales_contact_id == user.id,
        Contract.is_signed == True
    ).all()
    if not signed_contracts:
        click.echo("Aucun contrat signé disponible.")
        return
    click.echo("\nContrats signés disponibles :")
    for c in signed_contracts:
        click.echo(f"  ID {c.id} → Client: {c.client.full_name} | Total: {c.total_amount} €")
    contract_id = click.prompt("ID du contrat", type=int)
    event_name = click.prompt("Nom de l'événement")
    start_str = click.prompt("Date/heure de début (YYYY-MM-DD HH:MM)")
    end_str = click.prompt("Date/heure de fin (YYYY-MM-DD HH:MM)")
    location = click.prompt("Lieu (Entrée pour laisser vide)", default="")
    attendees = click.prompt("Nombre de participants attendus", type=int)
    notes = click.prompt("Notes (Entrée pour laisser vide)", default="")
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
        event = create_event(db, user, contract_id, event_name, start_date, end_date,
                             location or None, attendees, notes or None)
        click.echo(f"\nÉvénement créé avec succès ! ID: {event.id}")
    except ValueError as ve:
        click.echo(f"Erreur de format de date : {ve}")
    except Exception as e:
        click.echo(f"Erreur : {e}")


@require_role("gestion", "support")
def update_event_cmd():
    db: Session = next(get_db())
    user = get_current_user()
    event_id = click.prompt("ID de l'événement à modifier", type=int)
    updates = {}
    if click.confirm("Modifier le nom ?", default=False):
        updates["event_name"] = click.prompt("Nouveau nom")
    if click.confirm("Modifier la date de début ?", default=False):
        updates["start_date"] = datetime.strptime(click.prompt("Nouvelle date début (YYYY-MM-DD HH:MM)"), "%Y-%m-%d %H:%M")
    if click.confirm("Modifier la date de fin ?", default=False):
        updates["end_date"] = datetime.strptime(click.prompt("Nouvelle date fin (YYYY-MM-DD HH:MM)"), "%Y-%m-%d %H:%M")
    if click.confirm("Modifier le lieu ?", default=False):
        updates["location"] = click.prompt("Nouveau lieu (Entrée pour laisser vide)", default="")
    if click.confirm("Modifier le nombre de participants ?", default=False):
        updates["attendees"] = click.prompt("Nouveau nombre", type=int)
    if click.confirm("Modifier les notes ?", default=False):
        updates["notes"] = click.prompt("Nouvelles notes (Entrée pour laisser vide)", default="")
    if user.role == "gestion" and click.confirm("Attribuer/changer le support ?", default=False):
        supports = db.query(User).filter(User.role == "support").all()
        if supports:
            click.echo("Supports disponibles :")
            for s in supports:
                click.echo(f"  ID {s.id} → {s.full_name}")
            sid = click.prompt("ID du support (laisser vide pour aucun)", default=None)
            updates["support_contact_id"] = int(sid) if sid else None
    if updates:
        try:
            update_event(db, event_id, user, **updates)
            click.echo("\nÉvénement mis à jour avec succès !")
        except Exception as e:
            click.echo(f"Erreur : {e}")
    else:
        click.echo("Aucune modification apportée.")


@require_role("gestion")
def delete_event_cmd():
    db: Session = next(get_db())
    events = get_all_events(db)
    click.echo("\n=== Suppression d'un événement ===")
    if not events:
        click.echo("Aucun événement disponible.")
        return
    for e in events:
        start_fr = e.start_date.strftime("%d/%m/%Y %H:%M")
        click.echo(f"ID: {e.id} | {e.event_name} | Début: {start_fr}")
    event_id = click.prompt("ID de l'événement à supprimer", type=int)
    if click.confirm(f"⚠️  Confirmez la suppression de l'événement ID {event_id} ?", default=False):
        try:
            delete_event(db, get_current_user(), event_id)
            click.echo("Événement supprimé avec succès.")
        except Exception as e:
            click.echo(f"Erreur : {e}")


# ======================
# Menu interactif (dictionnaire en bas = plus de warnings Pylance)
# ======================
def interactive_menu():
    commands = {
        "list-users": list_users_cmd,
        "list-clients": list_clients_cmd,
        "create-client": create_client_cmd,
        "update-client": update_client_cmd,
        "delete-client": delete_client_cmd,
        "create-user": create_user_cmd,
        "update-user": update_user_cmd,
        "delete-user": delete_user_cmd,
        "list-contracts": list_contracts_cmd,
        "create-contract": create_contract_cmd,
        "update-contract": update_contract_cmd,
        "delete-contract": delete_contract_cmd,
        "list-events": list_events_cmd,
        "create-event": create_event_cmd,
        "update-event": update_event_cmd,
        "delete-event": delete_event_cmd,
        "list-unsigned-contracts": list_unsigned_contracts_cmd,
        "list-unpaid-contracts": list_unpaid_contracts_cmd,
        "list-events-without-support": list_events_without_support_cmd,
        "help": lambda: print_available_commands(),
        "quit": lambda: click.echo("\nAu revoir ! 👋")
    }

    def print_available_commands():
        user = get_current_user()
        role = user.role

        click.echo(f"\nBienvenue {user.full_name} ! Vous êtes connecté en tant que {role.upper()}.")
        click.echo("\n=== Commandes disponibles ===\n")

        click.echo("  list-users              → Voir tous les collaborateurs")
        click.echo("  list-clients            → Voir les clients")
        click.echo("  list-contracts          → Voir les contrats")
        click.echo("  list-events             → Voir les événements")
        click.echo("  list-unsigned-contracts → Contrats non signés")
        click.echo("  list-unpaid-contracts   → Contrats non payés entièrement")
        click.echo("  list-events-without-support → Événements sans support")

        if role == "commercial":
            click.echo("\n--- Vos actions commerciales ---")
            click.echo("  create-client           → Créer un nouveau client")
            click.echo("  update-client           → Modifier un de vos clients")
            click.echo("  delete-client           → Supprimer un de vos clients")
            click.echo("  create-contract         → Créer un contrat")
            click.echo("  update-contract         → Modifier un de vos contrats")
            click.echo("  create-event            → Créer un événement")

        if role == "support":
            click.echo("\n--- Vos actions support ---")
            click.echo("  update-event            → Mettre à jour vos événements")

        if role == "gestion":
            click.echo("\n--- Actions administratives ---")
            click.echo("  create-user             → Créer un collaborateur")
            click.echo("  update-user             → Modifier un collaborateur")
            click.echo("  delete-user             → Supprimer un collaborateur")
            click.echo("  create-client           → Créer un client")
            click.echo("  update-client           → Modifier un client")
            click.echo("  delete-client           → Supprimer un client")
            click.echo("  create-contract         → Créer un contrat")
            click.echo("  update-contract         → Modifier un contrat")
            click.echo("  delete-contract         → Supprimer un contrat")
            click.echo("  update-event            → Gérer les événements")
            click.echo("  delete-event            → Supprimer un événement")

        click.echo("\n  help                    → Afficher ce menu")
        click.echo("  quit                    → Quitter\n")

    print_available_commands()

    while True:
        try:
            cmd = click.prompt("\nCommande", type=str).strip().lower()
            if cmd in commands:
                if cmd == "quit":
                    commands[cmd]()
                    break
                commands[cmd]()
            else:
                click.echo("Commande inconnue. Tapez 'help'.")
        except click.Abort:
            click.echo("\n⚠️  Action annulée – retour au menu principal.")
        except Exception as e:
            click.echo(f"\nUne erreur inattendue s'est produite : {e}")
            try:
                from app.sentry_config import capture_exception
                capture_exception(e)
                click.echo("(L'erreur a été journalisée pour analyse.)")
            except ImportError:
                click.echo("(Sentry non disponible.)")