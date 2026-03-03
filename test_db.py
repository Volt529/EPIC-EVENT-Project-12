from app.database import engine, Base

print("Création des tables dans la base de données...")

Base.metadata.create_all(bind=engine)

print("Tables créées avec succès !")
print("Un fichier 'epic_events_crm.db' devrait apparaître à la racine du projet.")