import os
import requests

url = "https://cdn.jsdelivr.net/npm/dash-bootstrap-components@1.6.0/dist/dash-bootstrap-components.min.js"

# Chemin local pour sauvegarder le fichier
base_dir = "C:/Users/33682/PycharmProjects/DataTest/static/dash/component"
file_path = os.path.join(base_dir, "dash_bootstrap_components/_components/dash_bootstrap_components.min.js")
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Téléchargement du fichier
try:
    print(f"Téléchargement de dash_bootstrap_components.min.js depuis {url}...")
    response = requests.get(url)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)
    print(f"Sauvegardé dash_bootstrap_components.min.js dans {file_path}")
except Exception as e:
    print(f"Échec du téléchargement de dash_bootstrap_components.min.js: {e}")