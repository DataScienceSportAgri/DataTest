from datetime import datetime
from logging import warn
import re
import math
from typing import List

import numpy as np
from shapely.geometry import Polygon, box
from pandas import DataFrame
from sklearn.linear_model import ElasticNet, ElasticNetCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, RobustScaler
import plotly.graph_objs as go
from django.middleware.csrf import logger
from django.core.exceptions import ObjectDoesNotExist
import os
from pathlib import Path
from dashapp.utils.Vectorisation import create_spatiotemporal_vectors, generer_valeurs_aleatoires, calcul_valeurs_combinees
import geopandas as gpd
import pandas as pd
from .models import SelectedPoint
from DataTest import settings
from sklearn.model_selection import TimeSeriesSplit
from tqdm import tqdm

# Colonnes à exclure
EXCLUDE_COLS = {'longitude', 'latitude', 'Rendement', 'Point',
                'Geometry', 'point_id', 'date', 'parcelle', 'country', 'pays', 'numero_parcelle', 'Longitude', 'Latitude'}
base_path = os.path.join(settings.BASE_DIR, "dashapp", "saved_parcelle_for_dash")
def process_zone(zone_data, target_date, decay_rate=0.1):
    """Traite une zone individuelle avec pondération temporelle"""
    X = zone_data['X'].sort_index(level='date')
    y = zone_data['y'].sort_index(level='date')

    # Calcul des poids temporels
    dates = X.index.get_level_values('date')
    days_diff = (target_date - dates).days
    weights = np.exp(-decay_rate * days_diff)

    return X, y, weights


def train_feature_model(X_feature, dates, target_date):
    # Entraînement avec pondération exponentielle
    days_diff = (target_date - dates).dt.days
    weights = np.exp(-0.1 * days_diff)

    model = Pipeline([
        ('scaler', StandardScaler()),
        ('model', ElasticNet(alpha=0.5, l1_ratio=0.7))
    ])

    model.fit(X_feature, weights=weights)
    return model


def train_yield_model(feature_predictions, y):
    # Agrégation des prédictions par zone
    X_final = pd.concat(feature_predictions, axis=1)

    model = Pipeline([
        ('scaler', RobustScaler()),
        ('model', ElasticNetCV(cv=TimeSeriesSplit(3)))
    ])

    model.fit(X_final, y)
    return model


def create_parcelle_dataframe(
        codepays: str,
        numero_parcelle: str,
        nomdates: list = None
) -> pd.DataFrame:
    """
    Crée un dataframe filtré selon les nomdates spécifiés

    Args:
        codepays (str): Code pays (ex: 'AT')
        numero_parcelle (str): Numéro de parcelle (ex: '648038')
        nomdates (list): Liste optionnelle des nomdates à inclure [1][2]
        base_path (str): Chemin de base des données

    Returns:
        pd.DataFrame: DataFrame filtré avec colonnes [nomdate, datevisee, datereelle]
    """

    target_dir = Path(base_path) / f"{codepays}" / f"{numero_parcelle}"

    # Vérification du répertoire
    if not target_dir.is_dir():
        raise FileNotFoundError(f"Répertoire {target_dir} introuvable")

    # Pattern optimisé avec groupe de capture nommé
    pattern = re.compile(
        rf"^{re.escape(numero_parcelle)}"
        r"_X(?P<nomdate>.+?)X_"
        r"(?P<datevisee>\d{2}-\d{2}-\d{4})_"
        r"(?P<datereelle>\d{2}-\d{2}-\d{4})_encodee\.txt$"
    )

    data = []

    # Parcours des fichiers avec filtre
    for filepath in target_dir.glob("*.txt"):
        match = pattern.match(filepath.name)
        if match:
            nomdate = match.group('nomdate')

            # Filtrage par nomdates si spécifié [6]
            if nomdates and nomdate not in nomdates:
                continue

            data.append({
                'nomdate': nomdate,
                'datevisee': datetime.strptime(match.group('datevisee'), "%d-%m-%Y"),
                'datereelle': datetime.strptime(match.group('datereelle'), "%d-%m-%Y")
            })

    # Création du DataFrame avec gestion du cas vide
    df = pd.DataFrame(data)

    if not df.empty:
        return df.sort_values('datereelle').reset_index(drop=True)
    return df


def get_dates(parcelle, country, gdf):
    """Gestion unifiée de la récupération des dates"""
    if parcelle == 'Boulinsard':
        return gdf.index.get_level_values('date').unique().tolist()
    else:
        date_df = create_parcelle_dataframe(country, parcelle)
        return date_df['datereelle'].dt.date.tolist()



def load_points_data(session_id, noms_dates, noms_dates_boulinsard, indices, points_client):
    """
    Charge les données des points sauvegardés dans la session et sur le client,
    construit un DataFrame unifié avec tri temporel et sélection d'indices.

    Args:
        session_id (str): Identifiant de session pour récupérer les points sauvegardés.
        noms_dates (list): Liste des noms de dates normales à utiliser pour le tri.
        noms_dates_boulinsard (list): Liste des noms de dates Boulinsard à utiliser pour le tri.
        indices (list): Liste des indices à conserver dans le DataFrame.
        points_client (list): Liste des points encore présents sur le client.

    Returns:
        pd.DataFrame: DataFrame combiné et filtré.
    """

    try:
        # Récupération de tous les points de la session
        points_session = SelectedPoint.objects.filter(session_id=session_id)
    except ObjectDoesNotExist:
        return pd.DataFrame()

    if not points_session.exists():
        return pd.DataFrame()

        # Fusionner les points du client avec ceux de la session
    all_points = []
    for point in points_session:
        if any(
                p['latitude'] == point.latitude and p['longitude'] == point.longitude and p[
                    'parcelle'] == point.parcelle
                for p in points_client
        ):
            all_points.append(point)

    if not all_points:
        return pd.DataFrame()

    grouped_data = {}


    # Regroupement des points par parcelle pour optimisation I/O
    for point in all_points:
        key = (point.country_code, point.parcelle)
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(point)

    all_dfs = []

    # Traitement par groupe de parcelle
    for (country, parcelle), points_group in grouped_data.items():
        parcelle_path = os.path.join(base_path, country, parcelle, "utils", f"{str(parcelle)}_filtered.pkl")

        if not os.path.exists(parcelle_path):
            print(f"Fichier introuvable: {parcelle_path}")
            continue

        try:
            # Chargement du dataframe complet de la parcelle
            df = pd.read_pickle(parcelle_path)

            # Extraction des indexes spécifiques
            valid_indexes = [p.dataframe_index for p in points_group
                             if isinstance(p.dataframe_index, int)
                             and p.dataframe_index < len(df)]

            if not valid_indexes:
                continue

            # Filtrage des lignes correspondant aux indexes valides
            df_filtered = df.iloc[valid_indexes].copy()

            # Filtrage par noms de dates
            if 'date' in df.index.names:
                if noms_dates_boulinsard and 'boulinsard' in df.columns:
                    df_filtered = df_filtered[df_filtered['boulinsard'].isin(noms_dates_boulinsard)]
                elif noms_dates and 'date' in df.columns:
                    df_filtered = df_filtered[df_filtered['date'].isin(noms_dates)]

            # Sélection des colonnes spécifiées par les indices
            columns_to_keep = ['date'] + indices + ['Rendement']
            df_filtered = df_filtered[columns_to_keep]

            # Ajout des métadonnées géographiques
            df_filtered['parcelle'] = parcelle
            df_filtered['pountry'] = country

            # Ajout des coordonnées depuis les points
            coord_mapping = {p.dataframe_index: (p.latitude, p.longitude)
                             for p in points_group if p.dataframe_index in valid_indexes}
            df_filtered['Latitude'] = df_filtered.index.map(lambda x: coord_mapping.get(x, (None, None))[0])
            df_filtered['Longitude'] = df_filtered.index.map(lambda x: coord_mapping.get(x, (None, None))[1])

            all_dfs.append(df_filtered)

        except Exception as e:
            print(f"Erreur sur la parcelle {parcelle} : {str(e)}")
            continue

    if not all_dfs:
        return pd.DataFrame()

    # Fusion finale
    final_df = pd.concat(all_dfs, axis=0)

    # Tri temporel si colonne date existe
    if 'date' in final_df.columns:
        final_df = final_df.sort_values('date')

    # Réorganisation des colonnes finales
    column_order = ['country', 'parcelle', 'Latitude', 'Longitude', 'date', 'point_id'] + indices + ['Rendement']
    return final_df[column_order].reset_index(drop=True)


def load_filtered_data(country_codes, parcelles_dict_date, indices,
                       min_rendement, max_rendement, min_indice, max_indice):
    """
    Charge et filtre les données selon les critères spécifiés

    Args:
        country_codes (list): Liste des codes pays (ex: ['FR', 'DE'])
        parcelles (list): Liste des numéros de parcelles
        dates_boulinsard (list): Dates au format Boulinsard à inclure
        dates_normales (list): Dates normales à inclure
        indices (list): Liste des indices végétation à conserver
        min_rendement (float): Pourcentage minimal à exclure (0-100)
        max_rendement (float): Pourcentage maximal à exclure (0-100)
        min_indice (float): Pourcentage minimal de l'indice à exclure (0-100)
        max_indice (float): Pourcentage maximal de l'indice à exclure (0-100)

    Returns:
        pd.DataFrame: DataFrame combiné avec colonnes [country, parcelle, date] + indices + ['rendement']
    """
    base_path = os.path.join(settings.BASE_DIR, "dashapp", "saved_parcelle_for_dash")
    all_dfs = []
    target_indice = indices[0] if indices else None

    # Étape 2: Chargement des dataframes avec vérification des dossiers existants
    buffered_dfs = {}
    for country in country_codes:
        country_path = os.path.join(base_path, country)

        if not os.path.exists(country_path):
            warn(f"Dossier pays introuvable: {country_path}")
            continue

        # Liste des parcelles existantes pour ce pays
        existing_parcelles = [
            p for p in os.listdir(country_path)
            if os.path.isdir(os.path.join(country_path, p))
        ]
        parcelles = parcelles_dict_date.keys()
        # Filtrage avec les parcelles sélectionnées
        valid_parcelles = list(set(existing_parcelles) & set(parcelles))

        for parcelle in valid_parcelles:
            try:
                file_path = os.path.join(country_path, parcelle, "utils", f"{parcelle}_filtered.pkl")

                if not os.path.exists(file_path):
                    warn(f"Fichier parcelle introuvable: {file_path}")
                    continue

                try:
                    df = pd.read_pickle(file_path)

                    # Vérification des colonnes critiques
                    required_columns = ['Rendement'] + indices
                    missing_columns = [col for col in required_columns if col not in df.columns]

                    if missing_columns:
                        logger.warning(f"Colonnes manquantes dans {parcelle} : {', '.join(missing_columns)}")
                        continue

                    # Vérification de la colonne date dans l'index
                    if 'date' not in df.index.names and 'date' not in df.columns:
                        logger.warning(f"Colonne/Index 'date' manquant dans {parcelle}")
                        continue

                    dates = parcelles_dict_date[parcelle]
                    print('index de liste',df.index.get_level_values('date').isin(dates))
                    df = df.loc[df.index.get_level_values('date').isin(dates)]

                    # Calcul des seuils dynamiques
                    rendement_min = df['Rendement'].quantile(min_rendement / 100.0)
                    rendement_max = df['Rendement'].quantile(max_rendement / 100.0)
                    indice_min = df[target_indice].quantile(min_indice / 100.0) if target_indice else None
                    indice_max = df[target_indice].quantile(max_indice / 100.0) if target_indice else None

                    # Application des filtres
                    filters = [
                        df['Rendement'].between(rendement_min, rendement_max),
                    ]

                    if target_indice:
                        filters.append(df[target_indice].between(indice_min, indice_max))
                    print('filters',filters)
                    filtered_df = df[np.logical_and.reduce(filters)]

                    # Sélection des colonnes
                    print('indices',indices)
                    cols_to_keep = ['Rendement', 'Latitude', 'Longitude'] + indices
                    filtered_df = filtered_df[cols_to_keep].reset_index(level='point_id')
                    print('filtered_df',filtered_df)
                    filtered_df = filtered_df.reset_index()
                    # Ajout des métadonnées
                    filtered_df['country'] = country
                    filtered_df['parcelle'] = parcelle

                    all_dfs.append(filtered_df)

                except Exception as e:
                    warn(f"Erreur avec {file_path} : {str(e)}")
                    continue

            except Exception as e:
                warn(f"Erreur avec {file_path} : {str(e)}")
                continue

    if not all_dfs:
        return pd.DataFrame()

    final_df = pd.concat(all_dfs)

    # Réorganisation des colonnes
    column_order = ['country', 'parcelle', 'date', 'Latitude', 'Longitude', 'point_id'] + indices + ['Rendement']

    print('test index',final_df[column_order])
    return final_df[column_order]


def decouper_parcelle(gdf: gpd.GeoDataFrame, buffer_distance: float) -> gpd.GeoDataFrame:
    """
    Découpe une parcelle en sous-zones carrées avec gestion dynamique de la taille

    Args:
        gdf: GeoDataFrame des points de la parcelle
        buffer_distance: Distance totale du buffer initial

    Returns:
        GeoDataFrame avec colonne 'sous_zone' et géométries des sous-zones
    """
    # Calcul dynamique de la taille des sous-zones
    cell_size = buffer_distance / 10

    # Création d'une grille régulière
    bounds = gdf.total_bounds
    x_coords = np.arange(bounds[0], bounds[2], cell_size)
    y_coords = np.arange(bounds[1], bounds[3], cell_size)

    # Génération des polygones de sous-zones
    sous_zones = []
    for x in x_coords:
        for y in y_coords:
            polygon = Polygon([
                (x, y),
                (x + cell_size, y),
                (x + cell_size, y + cell_size),
                (x, y + cell_size)
            ])
            if gdf.intersects(polygon).any():
                sous_zones.append(polygon)

    # Création du GeoDataFrame des sous-zones
    return gpd.GeoDataFrame(
        geometry=sous_zones,
        crs=gdf.crs
    ).reset_index().rename(columns={'index': 'sous_zone_id'})


def assigner_points_sous_zones(gdf_points: gpd.GeoDataFrame, gdf_zones: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Associe chaque point à sa sous-zone avec jointure spatiale
    """
    return gpd.sjoin(
        gdf_points,
        gdf_zones,
        how='inner',
        predicate='within'
    ).reset_index(drop=True)


def create_long_format_ts(sous_zone_group: pd.DataFrame, dates) -> pd.DataFrame:
    """
    Transforme un DataFrame MultiIndex existant en format long avec les colonnes demandées

    Args:
        sous_zone_group: DataFrame avec :
            - Index: MultiIndex (date, point_id)
            - Colonnes: latitude, longitude, [features...]

    Returns:
        DataFrame avec colonnes :
            point_id, latitude, longitude, jours_depuis_debut, feature_value
    """
    # Réinitialisation de l'index pour accéder aux dates et point_id
    new_df = []
    for point_id_idx, point_id_df in sous_zone_group.groupby(['point_id']):
        point_id_df = point_id_df.reset_index()
        print('test point id df',point_id_df)
        feature_col = point_id_df.columns[5]
        point_id = point_id_idx
        lat = point_id_df.loc[0,'Latitude']
        long = point_id_df.loc[0,'Longitude']
        # Calcul des jours depuis la première date
        min_date = min(dates)
        a=0
        print('len(dates)',len(dates))
        for date in dates:
            try:
                newrow = {
                'point_id' : point_id,
                'jours_depuis_debut': (date - min_date).days,
                'feature_value' : point_id_df.loc[a, feature_col],  # Accès via nom
                'latitude' : lat,
                'longitude' : long
                }
            except:
                break
            a+=1
            print('date',date)
            new_df.append(newrow)
    print('temporalserie',pd.DataFrame(new_df))
    # Sélection et ordonnancement des colonnes
    return pd.DataFrame(new_df)



def vectorize_data(data: pd.DataFrame, buffer_distance: float = 500, microbuffer: float = 50) -> DataFrame:

    country_crs = {
        'FR': 'EPSG:2154',  # Nord de la France (RGF93 v1 / Lambert-93)
        'AT': 'EPSG:31256',  # Autriche (MGI Austria Lambert)
        'EE': 'EPSG:3879',  # Estonie (ETRS89 / Eesti TM)
        'LV': 'EPSG:3826'  # Lettonie (LKS94 / Latvia TM)
    }

    def get_country_crs(country_code: str) -> str:
        """Retourne le CRS approprié avec validation"""
        crs = country_crs.get(country_code.upper())
        if not crs:
            raise ValueError(f"CRS non défini pour le pays : {country_code}")
        return crs

    # Utilisation dans la fonction de projection
    def project_gdf(gdf: gpd.GeoDataFrame, country_code: str) -> gpd.GeoDataFrame:
        """Reprojette le GeoDataFrame selon le code pays"""
        return gdf.to_crs(get_country_crs(country_code))
    print('data',data)
    features = data.columns.difference(EXCLUDE_COLS).tolist()
    vector_data = pd.DataFrame(columns=[['country','parcelle','point_id','longitude','latitude'] + features + ['Rendement']])
    # Itération par groupe parcelle/pays
    for (parcelle, country), group in tqdm(data.groupby(['parcelle', 'country']),
                                          desc="Processing zones"):
        # Conversion en GeoDataFrame
        gdf = gpd.GeoDataFrame(
            group,
            geometry=gpd.points_from_xy(group['Longitude'], group['Latitude']),
            crs="EPSG:4326"  # WGS84 standard
        ).pipe(project_gdf, country_code=country)
        # Récupération des dates selon le type de parcelle

        # Récupération des dates
        dates = get_dates(parcelle, country, gdf)
        print('dates',dates)
        # Découpage en sous-zones géométriques
        gdf_sous_zones = decouper_parcelle(gdf, buffer_distance)

        # Association des points aux sous-zones
        gdf_zone_points = assigner_points_sous_zones(gdf, gdf_sous_zones)

        # Itération sur les sous-zones
        for sous_zone_id, gdf_sous_zone in gdf_zone_points.groupby('sous_zone_id'):


            Rendements = gdf_sous_zone['Rendement'].tolist()
            print('sous_zone_groupe',gdf_sous_zone)
            # Itération sur les caractéristiques
            for feature in tqdm(features,desc=f"{parcelle}-{country}"):
                # Agrégation spatiale et temporelle
                # À l'intérieur de votre boucle sur les sous_zones :

                print('sous_zone_groupe',gdf_sous_zone[['point_id','Latitude','Longitude', 'date']+[feature]])
                time_series_df = create_long_format_ts(gdf_sous_zone[['point_id','Latitude','Longitude', 'date']+[feature]], dates)
                # Transformation du format long vers wide
                df_wide = time_series_df.pivot_table(
                    index=['point_id', 'latitude', 'longitude'],
                    columns='jours_depuis_debut',
                    values='feature_value',
                    aggfunc='first'  # À remplacer par mean() si valeurs multiples
                ).reset_index()
                print('df_wide',df_wide)
                # Exemple de sortie :
                a = 0
                gdf_wide = gpd.GeoDataFrame(
                    df_wide,
                    geometry=gpd.points_from_xy(df_wide['longitude'], df_wide['latitude']),
                    crs="EPSG:4326"  # WGS84 standard
                ).pipe(project_gdf, country_code=country)
                print('gdf_wide',gdf_wide)
                for idx, point in gdf_wide.iterrows():

                    # Création du buffer unique pour la zone
                    buffer = point.geometry.buffer(microbuffer)
                    # Filtrage des points dans le rayon
                    points_around = gdf_wide[gdf_wide.geometry.within(buffer)]
                    print('points_around',points_around)
                    vectors = create_spatiotemporal_vectors(point, points_around, dates)
                    print('vectors',vectors)
                    vector_data.loc[len(vector_data),'country'] = country
                    vector_data.loc[len(vector_data),'parcelle'] = parcelle
                    vector_data.loc[len(vector_data),'point_id'] = df_wide['point_id']
                    vector_data.loc[len(vector_data),'latitude'] = df_wide['latitude']
                    vector_data.loc[len(vector_data),'longitude'] = df_wide['longitude']
                    vector_data.loc[len(vector_data),features] = vectors
                    vector_data.loc[len(vector_data),'Rendement'] = Rendements[a]
                    a+=1
                print('vector_data',vector_data)

    return vector_data


class AveragedElasticNet:
    """Méta-modèle qui moyenne les coefficients de plusieurs modèles ElasticNet"""

    def __init__(self, models: List[ElasticNet]):
        self.models = models
        self.coef_ = np.mean([m.coef_ for m in models], axis=0)
        self.intercept_ = np.mean([m.intercept_ for m in models], axis=0)

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.models], axis=0)

def train_ElasticNet_model(vectors_dataframe, centroidvalue, arrivalvalue, comb):
    nvalue = int(math.sqrt(comb))
    centroidvalues = generer_valeurs_aleatoires(centroidvalue, n=nvalue)
    arrivalvalues = generer_valeurs_aleatoires(arrivalvalue, n=nvalue)
    features = vectors_dataframe.columns.difference(EXCLUDE_COLS)
    models = []
    for centroid in centroidvalues:
        for arrival in arrivalvalues:
            dataiteration = vectors_dataframe[features].apply(
                lambda row: calcul_valeurs_combinees(
                    centroid=centroid,
                    arrivee=arrival,
                    vecteurs=row
                ),
                axis=1
            )
            # Préparation des données
            X = np.vstack(dataiteration)
            y = vectors_dataframe['Rendement']
            # Entraînement du modèle
            model = ElasticNet()
            model.fit(X, y)
            models.append(model)
    # Création du méta-modèle moyenné
    return AveragedElasticNet(models) if models else None

def create_3d_feature_space(X, y, coef, intercept):
    features = sorted(zip(X.columns, coef), key=lambda x: abs(x[1]), reverse=True)[:3]
    if len(features) < 3:
        return None

    feat_names = [f[0] for f in features]
    x_grid, y_grid = np.meshgrid(np.linspace(X[feat_names[0]].min(), X[feat_names[0]].max(), 20),
                                 np.linspace(X[feat_names[1]].min(), X[feat_names[1]].max(), 20))

    z_grid = intercept + coef[0] * x_grid + coef[1] * y_grid + coef[2] * X[feat_names[2]].mean()

    return go.Figure(
        data=[
            go.Scatter3d(
                x=X[feat_names[0]], y=X[feat_names[1]], z=X[feat_names[2]],
                mode='markers',
                marker=dict(color=y, colorscale='Viridis', size=5)
            ),
            go.Surface(x=x_grid, y=y_grid, z=z_grid, opacity=0.7)
        ],
        layout=go.Layout(
            scene=dict(
                xaxis_title=feat_names[0],
                yaxis_title=feat_names[1],
                zaxis_title=feat_names[2]
            )
        )
    )


def predict_elasticnet(model, X_data):
    """
    Effectue des prédictions à partir de données déjà préparées par les vues

    Args:
        model (dict): Modèle entraîné contenant :
            - 'pipeline': Pipeline sklearn entraîné
            - 'features': Liste des caractéristiques utilisées
        X_data (pd.DataFrame): Données préparées par la vue avec les colonnes nécessaires

    Returns:
        dict: Résultats des prédictions avec statistiques
    """
    try:
        # Vérification de la compatibilité des caractéristiques
        missing_features = set(model['features']) - set(X_data.columns)
        if missing_features:
            raise ValueError(f"Caractéristiques manquantes : {missing_features}")

        # Sélection des caractéristiques du modèle
        X_pred = X_data[model['features']].copy()

        # Prédictions
        predictions = model['pipeline'].predict(X_pred)

        # Conversion des résultats
        return {
            'predictions': predictions.tolist(),
            'stats': {
                'mean': float(np.nanmean(predictions)),
                'std': float(np.nanstd(predictions)),
                'min': float(np.nanmin(predictions)),
                'max': float(np.nanmax(predictions)),
                'q25': float(np.nanquantile(predictions, 0.25)),
                'q75': float(np.nanquantile(predictions, 0.75))
            },
            'sample_data': {
                'features': model['features'],
                'example_prediction': predictions[0] if len(predictions) > 0 else None
            }
        }

    except Exception as e:
        error_msg = f"Erreur de prédiction : {str(e)}"
        print(error_msg)
        return {'error': error_msg}


