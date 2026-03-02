import bcrypt
from sqlalchemy.orm import Session
from .models import User
from .database import get_db


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe correspond au hash stocké"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_user(db: Session, username: str, password: str, full_name: str, role: str) -> User:
    """Crée un nouvel utilisateur (utilisé surtout par le rôle gestion)"""
    if db.query(User).filter(User.username == username).first():
        raise ValueError("Ce nom d'utilisateur existe déjà.")

    hashed_pw = hash_password(password)
    user = User(
        username=username,
        password_hash=hashed_pw,
        full_name=full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Authentifie un utilisateur et retourne l'objet User si OK, sinon None"""
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None