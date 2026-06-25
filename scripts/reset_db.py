import os
import sys

# Add the project root to sys.path so we can import backend.app
sys.path.append(os.getcwd())

from backend.app.database import reset_knowledge_base, settings

if __name__ == "__main__":
    print("Starting full knowledge base reset...")
    reset_knowledge_base()

    # Also delete the DB file to force schema recreation if needed
    if settings.database_url.exists():
        print(f"Deleting database file at {settings.database_url}")
        settings.database_url.unlink()

    print("Reset complete.")
