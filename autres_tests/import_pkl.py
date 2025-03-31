import os
from pathlib import Path
import pandas as pd
import shutil

# Configuration des chemins
PYCHARM_PROJECTS = Path.home() / 'PycharmProjects'
SRC_ROOT = PYCHARM_PROJECTS / 'export_dataframe_in_parquet'
DST_ROOT = PYCHARM_PROJECTS / 'DataTest' / 'dashapp' / 'saved_parcelle_for_dash'

def convert_parquet_to_pickle(src_path, dst_path):
    """Convertit un fichier .parquet en .pkl"""
    try:
        df = pd.read_parquet(src_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_pickle(dst_path, protocol=4)
        print(f"Conversion réussie : {src_path} -> {dst_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la conversion de {src_path.name} : {str(e)}")
        return False

def clean_utils_folder(utils_dir):
    """Supprime uniquement les fichiers dans utils après conversion"""
    for file in utils_dir.iterdir():
        if file.is_file():  # Supprime uniquement les fichiers
            print(f"Suppression du fichier : {file}")
            file.unlink()

def process_files():
    """Traite les fichiers .parquet dans utils et conserve le reste"""
    success = 0
    errors = 0

    for utils_dir in SRC_ROOT.glob('**/utils'):
        for parquet_file in utils_dir.glob('*.parquet'):
            relative_path = parquet_file.relative_to(SRC_ROOT)
            pickle_path = DST_ROOT / relative_path.with_suffix('.pkl')

            if convert_parquet_to_pickle(parquet_file, pickle_path):
                success += 1
            else:
                errors += 1

        # Nettoyer le dossier utils après conversion
        clean_utils_folder(utils_dir)

    return success, errors

if __name__ == "__main__":
    print("Traitement des fichiers...")
    success, errors = process_files()
    print(f"\nRésultat : {success} conversions réussies, {errors} erreurs")
#%%
import pandas as pd
from pathlib import Path

# Configuration des chemins
PYCHARM_PROJECTS = Path.home() / 'PycharmProjects'
SRC_ROOT = PYCHARM_PROJECTS / 'export_dataframe_in_parquet'
DST_ROOT = PYCHARM_PROJECTS / 'DataTest' / 'dashapp' / 'saved_parcelle_for_dash'

def convert_dates_visee(src_root, dst_root):
    """Convertit dates_visee.pkl de SRC_ROOT vers DST_ROOT"""
    src_file = src_root / 'dates_visee.parquet'
    dst_file = dst_root / 'dates_visee.pkl'

    try:
        if src_file.exists():
            # Charger le fichier source
            df = pd.read_parquet(src_file)

            # Créer le dossier de destination si nécessaire
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # Sauvegarder le fichier au format pickle dans le dossier de destination
            df.to_pickle(dst_file, protocol=4)
            print(f"Conversion réussie : {src_file} -> {dst_file}")
        else:
            print(f"Le fichier source n'existe pas : {src_file}")
    except Exception as e:
        print(f"Erreur lors de la conversion : {str(e)}")

if __name__ == "__main__":
    convert_dates_visee(SRC_ROOT, DST_ROOT)
