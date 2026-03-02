from sqlalchemy.orm import Session
from app.models import User, Client, Contract, Event
from app.auth import hash_password
from datetime import datetime


# ======================
# CRUD UTILISATEURS
# ======================

def get_all_users(db: Session):
    return db.query(User).all()


def create_collaborator(db: Session, username: str, password: str, full_name: str, role: str) -> User:
    if role not in ["gestion", "commercial", "support"]:
        raise ValueError("Rôle invalide.")
    if db.query(User).filter(User.username == username).first():
        raise ValueError("Nom d'utilisateur déjà pris.")

    hashed = hash_password(password)
    user = User(username=username, password_hash=hashed, full_name=full_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, current_user: User, user_id: int):
    if current_user.role != "gestion":
        raise PermissionError("Seul le rôle gestion peut supprimer un collaborateur.")
    if current_user.id == user_id:
        raise PermissionError("Vous ne pouvez pas supprimer votre propre compte.")
    
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise ValueError("Collaborateur non trouvé.")
    
    db.delete(user_to_delete)
    db.commit()
    return True


# ======================
# CRUD CLIENTS
# ======================

def get_all_clients(db: Session):
    return db.query(Client).all()


def get_clients_by_sales(db: Session, sales_user_id: int):
    return db.query(Client).filter(Client.sales_contact_id == sales_user_id).all()


def create_client(db: Session, current_user: User, full_name: str, email: str, phone: str = None, company: str = None) -> Client:
    client = Client(
        full_name=full_name,
        email=email,
        phone=phone,
        company=company,
        sales_contact_id=current_user.id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, current_user: User, client_id: int, **updates):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Client non trouvé.")
    if current_user.role == "commercial" and client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez modifier que vos propres clients.")
    if current_user.role not in ["gestion", "commercial"]:
        raise PermissionError("Accès refusé.")

    allowed = ["full_name", "email", "phone", "company", "sales_contact_id"]
    for key, value in updates.items():
        if key in allowed:
            setattr(client, key, value or None if key in ["phone", "company"] else value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, current_user: User, client_id: int):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Client non trouvé.")
    
    if current_user.role == "commercial" and client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez supprimer que vos propres clients.")
    if current_user.role not in ["gestion", "commercial"]:
        raise PermissionError("Accès refusé.")
    
    db.delete(client)
    db.commit()
    return True


# ======================
# CRUD CONTRATS
# ======================

def get_all_contracts(db: Session):
    return db.query(Contract).all()


def create_contract(db: Session, current_user: User, client_id: int, total_amount: float,
                    remaining_amount: float, is_signed: bool = False) -> Contract:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("Client non trouvé.")

    if current_user.role == "commercial" and client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez créer un contrat que pour vos clients.")

    contract = Contract(
        client_id=client_id,
        sales_contact_id=client.sales_contact_id,
        total_amount=total_amount,
        remaining_amount=remaining_amount,
        is_signed=is_signed
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def get_unsigned_contracts(db: Session):
    return db.query(Contract).filter(Contract.is_signed == False).all()


def get_unpaid_contracts(db: Session):
    return db.query(Contract).filter(Contract.remaining_amount > 0).all()


def update_contract(db: Session, current_user: User, contract_id: int, **updates):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("Contrat non trouvé.")
    if current_user.role == "commercial" and contract.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez modifier que vos propres contrats.")
    if current_user.role not in ["gestion", "commercial"]:
        raise PermissionError("Accès refusé.")

    allowed = ["total_amount", "remaining_amount", "is_signed"]
    for key, value in updates.items():
        if key in allowed:
            setattr(contract, key, value)

    db.commit()
    db.refresh(contract)
    return contract


def delete_contract(db: Session, current_user: User, contract_id: int):
    if current_user.role != "gestion":
        raise PermissionError("Seul le rôle gestion peut supprimer un contrat.")
    
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("Contrat non trouvé.")
    
    db.delete(contract)
    db.commit()
    return True


# ======================
# CRUD ÉVÉNEMENTS
# ======================

def get_all_events(db: Session):
    return db.query(Event).all()


def get_events_by_support(db: Session, support_user_id: int):
    return db.query(Event).filter(Event.support_contact_id == support_user_id).all()


def get_events_without_support(db: Session):
    return db.query(Event).filter(Event.support_contact_id.is_(None)).all()


def create_event(db: Session, current_user: User, contract_id: int, event_name: str,
                 start_date: datetime, end_date: datetime,
                 location: str = None, attendees: int = 0, notes: str = None) -> Event:
    if current_user.role != "commercial":
        raise PermissionError("Seuls les commerciaux peuvent créer des événements.")

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError("Contrat non trouvé.")
    if not contract.is_signed:
        raise PermissionError("L'événement ne peut être créé que sur un contrat signé.")
    if contract.client.sales_contact_id != current_user.id:
        raise PermissionError("Vous ne pouvez créer un événement que pour vos clients.")

    event = Event(
        event_name=event_name,
        contract_id=contract_id,
        start_date=start_date,
        end_date=end_date,
        location=location,
        attendees=attendees,
        notes=notes
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event_id: int, current_user: User, **updates):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError("Événement non trouvé.")

    if current_user.role == "support":
        if event.support_contact_id != current_user.id:
            raise PermissionError("Vous ne pouvez modifier que vos propres événements.")

    allowed = ["event_name", "start_date", "end_date", "location", "attendees", "notes", "support_contact_id"]
    for key, value in updates.items():
        if key in allowed:
            setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, current_user: User, event_id: int):
    if current_user.role != "gestion":
        raise PermissionError("Seul le rôle gestion peut supprimer un événement.")
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError("Événement non trouvé.")
    
    db.delete(event)
    db.commit()
    return True