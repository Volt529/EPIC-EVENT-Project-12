from app.database import SessionLocal, engine, Base
from app.auth import create_user
from app.models import User

# Recréer les tables au cas où (normalement déjà fait)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("Création du premier utilisateur administrateur (rôle gestion)")

username = input("Nom d'utilisateur (ex: admin) : ") or "admin"
password = input("Mot de passe (ex: admin123) : ") or "admin123"
full_name = input("Nom complet (ex: Dawn Stanley) : ") or "Dawn Stanley"

try:
    user = create_user(
        db=db,
        username=username,
        password=password,
        full_name=full_name,
        role="gestion"
    )
    print(f"\nUtilisateur créé avec succès !")
    print(f"Username : {user.username}")
    print(f"Rôle     : {user.role}")
    print(f"Nom      : {user.full_name}")
    print("\nVous pouvez maintenant vous connecter avec ces identifiants.")
except ValueError as e:
    print(f"Erreur : {e}")
finally:
    db.close()