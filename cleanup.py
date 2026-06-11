import os
import shutil

# Target directory
APP_DIR = "backend/app"

# Clean up existing subdirectories inside backend/app
for item in os.listdir(APP_DIR):
    item_path = os.path.join(APP_DIR, item)
    if os.path.isdir(item_path) and item not in ["__pycache__"]:
        shutil.rmtree(item_path)
    elif os.path.isfile(item_path) and item.endswith(".py"):
        os.remove(item_path)

print("Cleaned up old files.")
