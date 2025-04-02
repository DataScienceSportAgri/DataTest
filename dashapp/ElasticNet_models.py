from logging import warn

import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import plotly.graph_objs as go
from django.core.exceptions import ObjectDoesNotExist
import os
import pandas as pd
from glob import glob
from .models import SelectedPoint
from DataTest import settings

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
    base_path = "saved_parcelle_for_dash"

    # Regroupement des points par parcelle pour optimisation I/O
    for point in all_points:
        key = (point.country_code, point.parcelle)
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(point)

    all_dfs = []

    # Traitement par groupe de parcelle
    for (country, parcelle), points_group in grouped_data.items():
        parcelle_path = os.path.join(base_path, country, parcelle, "utils", "filtered_dataframe.pkl")

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
            df_filtered['Parcelle'] = parcelle
            df_filtered['Country'] = country

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
    column_order = ['Country', 'Parcelle', 'Latitude', 'Longitude', 'date'] + indices + ['Rendement']
    return final_df[column_order].reset_index(drop=True)


def load_filtered_data(country_codes, parcelles, dates_boulinsard, dates_normales, indices,
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

    for country in country_codes:
        for parcelle in parcelles:
            file_path = os.path.join(base_path, country, str(parcelle), "utils", "filtered_dataframe.pkl")

            if not os.path.exists(file_path):
                warn(f"Fichier introuvable : {file_path}")
                continue

            try:
                df = pd.read_pickle(file_path)

                # Vérification de la structure
                if not isinstance(df, pd.DataFrame) or df.empty:
                    warn(f"DataFrame vide ou invalide : {file_path}")
                    continue

                # Gestion des dates
                date_filter = []
                if dates_boulinsard and 'date_boulinsard' in df.columns:
                    date_filter.extend(dates_boulinsard)
                if dates_normales and 'date' in df.columns:
                    date_filter.extend(dates_normales)

                if date_filter:
                    if 'date' in df.index.names:
                        df = df[df.index.get_level_values('date').isin(date_filter)]
                    elif 'date' in df.columns:
                        df = df[df['date'].isin(date_filter)]

                # Calcul des seuils dynamiques
                rendement_min = df['rendement'].quantile(min_rendement / 100.0)
                rendement_max = df['rendement'].quantile(max_rendement / 100.0)
                indice_min = df[target_indice].quantile(min_indice / 100.0) if target_indice else None
                indice_max = df[target_indice].quantile(max_indice / 100.0) if target_indice else None

                # Application des filtres
                filters = [
                    df['rendement'].between(rendement_min, rendement_max),
                ]

                if target_indice:
                    filters.append(df[target_indice].between(indice_min, indice_max))

                filtered_df = df[np.logical_and.reduce(filters)]

                # Sélection des colonnes
                cols_to_keep = ['date', 'rendement'] + indices
                filtered_df = filtered_df[cols_to_keep].reset_index()

                # Ajout des métadonnées
                filtered_df['country'] = country
                filtered_df['parcelle'] = parcelle

                all_dfs.append(filtered_df)

            except Exception as e:
                warn(f"Erreur avec {file_path} : {str(e)}")
                continue

    if not all_dfs:
        return pd.DataFrame()

    final_df = pd.concat(all_dfs, ignore_index=True)

    # Réorganisation des colonnes
    column_order = ['country', 'parcelle', 'date'] + indices + ['rendement']
    return final_df[column_order]

def train_elasticnet_model(data):
    # Conversion des données
    X = pd.DataFrame(data['X'])
    y = pd.Series(data['y'])

    # Pipeline d'entraînement
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42))
    ])

    # Entraînement et validation
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='neg_mean_squared_error')
    pipeline.fit(X, y)

    # Récupération des résultats
    coefficients = pipeline.named_steps['model'].coef_
    intercept = pipeline.named_steps['model'].intercept_

    return {
        'pipeline': pipeline,
        'cv_rmse': np.sqrt(-cv_scores.mean()),
        'r2': pipeline.score(X, y),
        'feature_importance': dict(zip(data['features'], coefficients)),
        '3d_plot': create_3d_feature_space(X, y, coefficients, intercept)
    }


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

def predict_elasticnet(model_dict, X_new):
    X_scaled = model_dict['scaler'].transform(X_new)
    return model_dict['model'].predict(X_scaled)
