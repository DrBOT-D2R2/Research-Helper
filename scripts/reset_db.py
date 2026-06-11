import sys
import os

# Add the project root to sys.path so we can import backend.app
sys.path.append(os.getcwd())

from backend.app.database import reset_knowledge_base

if __name__ == "__main__":
    print("Starting full knowledge base reset...")
    reset_knowledge_base()
    print("Reset complete.")
