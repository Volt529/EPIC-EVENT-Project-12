from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Chemin vers la base de données SQLite (fichier qui sera créé dans le dossier du projet)
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR}/epic_events_crm.db"

# Création du moteur SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Nécessaire uniquement pour SQLite en multi-thread
    echo=False  # Mettre à True si tu veux voir toutes les requêtes SQL dans la console (utile pour debug)
)

# Factory pour créer des sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour tous les modèles
Base = declarative_base()


# Fonction utilitaire pour obtenir une session (on l'utilisera partout)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()