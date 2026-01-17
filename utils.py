import os
import shutil
import zipfile
import tempfile
import json

def save_uploaded_file(uploaded_file):
    """Saves uploaded file to a temporary directory."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        return None

def cleanup_temp_files(file_paths):
    """Removes temporary files."""
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

def create_zip_archive(file_paths, zip_name="generated_reels.zip"):
    """Creates a zip archive from a list of files."""
    zip_path = os.path.join(tempfile.gettempdir(), zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_paths:
            if os.path.exists(file):
                zipf.write(file, os.path.basename(file))
    return zip_path

CONFIG_FILE = "config.json"

def load_config():
    """Loads configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(key, value):
    """Saves a key-value pair to the configuration file."""
    config = load_config()
    config[key] = value
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")
