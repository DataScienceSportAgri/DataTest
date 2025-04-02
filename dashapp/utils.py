# utils.py
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import os


def get_dataframe(country_code, parcelle):
    """
    Charge le DataFrame correspondant au code pays et à la parcelle.
    Retourne un GeoDataFrame avec index spatial.
    """
    # Chemin vers les données
    base_path = "saved_parcelle_for_dash"
    file_path = os.path.join(base_path, country_code, parcelle, "utils", "filtered_dataframe.pkl")

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        print(f"Fichier introuvable: {file_path}")
        return None

    try:
        # Charger le DataFrame
        df = pd.read_pickle(file_path)

        # Convertir en GeoDataFrame si nécessaire
        if not isinstance(df, gpd.GeoDataFrame):
            if 'geometry' not in df.columns:
                # Créer une colonne geometry à partir des coordonnées
                geometry = [Point(lon, lat) for lon, lat in zip(df['Longitude'], df['Latitude'])]
                df = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            else:
                df = gpd.GeoDataFrame(df, crs="EPSG:4326")

        # Projeter en UTM pour des calculs de distance précis
        df = df.to_crs(epsg=32631)  # UTM zone 31N (Europe occidentale)

        return df

    except Exception as e:
        print(f"Erreur lors du chargement du DataFrame: {str(e)}")
        return None


def find_closest_point(df, lat, lon, max_distance=10):
    """
    Trouve le point le plus proche dans le DataFrame.

    Args:
        df: GeoDataFrame contenant les points
        lat: Latitude du point de référence
        lon: Longitude du point de référence
        max_distance: Distance maximale en mètres

    Returns:
        Dictionnaire contenant les informations du point le plus proche
        ou None si aucun point n'est trouvé
    """
    if df is None or df.empty:
        return None

    # Créer un point de référence
    ref_point = Point(lon, lat)

    # Convertir en GeoSeries avec projection UTM
    ref_geoseries = gpd.GeoSeries([ref_point], crs="EPSG:4326").to_crs(df.crs)

    # Calculer les distances
    distances = df.geometry.distance(ref_geoseries[0])

    # Trouver l'index du point le plus proche
    if distances.min() <= max_distance:
        closest_idx = distances.idxmin()
        closest_row = df.loc[closest_idx]

        # Convertir les coordonnées en WGS84 pour le stockage
        point_wgs84 = closest_row.geometry.to_crs("EPSG:4326")

        return {
            'index': closest_idx,
            'lat': point_wgs84.y,
            'lon': point_wgs84.x,
            'rendement': float(closest_row.get('Rendement', np.nan)),
            'ndvi': float(closest_row.get('NDVI', np.nan))
        }

    return None

def get_all_parcelle_numbers(country_code):
    """Liste toutes les parcelles disponibles pour un pays donné"""
    base_dir = os.path.join("saved_parcelle_for_dash", country_code)
    if not os.path.exists(base_dir):
        return []
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]