from app.database import SessionLocal
from app.auth import authenticate_user

db = SessionLocal()

username = input("Username : ")
password = input("Password : ")

user = authenticate_user(db, username, password)

if user:
    print(f"\nConnexion réussie !")
    print(f"Bienvenue {user.full_name} ({user.role})")
else:
    print("Identifiants incorrects")

db.close()
