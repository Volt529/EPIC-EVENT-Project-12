from app.sentry_config import capture_exception
import app.sentry_config  # initialise Sentry au démarrage
from app.cli import cli

if __name__ == "__main__":
    cli()
