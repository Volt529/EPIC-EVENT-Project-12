import sentry_sdk
import os
from dotenv import load_dotenv

# Charge le fichier .env à la racine
load_dotenv()

# Initialisation de Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment="development",  # ou "production" plus tard
)

# Fonction pour capturer manuellement une exception
def capture_exception(error):
    sentry_sdk.capture_exception(error)