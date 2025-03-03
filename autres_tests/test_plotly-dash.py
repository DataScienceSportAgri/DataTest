import os

def check_dash_bootstrap_npm():
    npm_path = os.path.join(os.getcwd(), 'node_modules', 'dash-bootstrap-components', 'dist')
    if os.path.exists(npm_path):
        files = os.listdir(npm_path)
        return f"Fichiers trouvés : {files}"
    return "dash-bootstrap-components n'est pas installé via npm"

print(check_dash_bootstrap_npm())