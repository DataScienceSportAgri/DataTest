import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import plotly.graph_objs as go

import os
import pandas as pd
from glob import glob


def load_filtered_data(country_code, parcelles, dates, rendement_min, rendement_max, indice_name, indice_min,
                       indice_max):
    """
    Charge et filtre les données depuis la structure de fichiers organisée.

    Args:
        country_code (str): Code pays (ex: 'FR')
        parcelles (list): Liste des numéros de parcelles
        dates (list): Liste des dates au format 'YYYY-MM-DD'
        rendement_min (float): Rendement minimum à filtrer
        rendement_max (float): Rendement maximum à filtrer
        indice_name (str): Nom de l'indice végétation à filtrer
        indice_min (float): Valeur minimale de l'indice
        indice_max (float): Valeur maximale de l'indice

    Returns:
        pd.DataFrame: DataFrame combiné et filtré
    """

    base_path = "saved_parcelle_for_dash"
    all_dfs = []

    for parcelle in parcelles:
        # Construction du chemin
        parcelle_path = os.path.join(base_path, country_code, str(parcelle), "utils", "filtered_dataframe.pkl")

        # Vérification de l'existence du fichier
        if not os.path.exists(parcelle_path):
            print(f"Fichier introuvable pour {parcelle} : {parcelle_path}")
            continue

        try:
            # Chargement du DataFrame
            df = pd.read_pickle(parcelle_path)

            # Vérification du format des données
            if not isinstance(df, pd.DataFrame) or df.empty:
                print(f"Format invalide pour {parcelle}")
                continue

            # Filtrage des dates (suppose un MultiIndex avec 'date')
            if 'date' in df.index.names:
                df = df[df.index.get_level_values('date').isin(dates)]

            # Filtrage des valeurs
            filtered = df[
                (df['Rendement'].between(rendement_min, rendement_max)) &
                (df[indice_name].between(indice_min, indice_max))
                ]

            # Ajout des métadonnées
            filtered['Parcelle'] = parcelle
            filtered['Country'] = country_code

            all_dfs.append(filtered)

        except Exception as e:
            print(f"Erreur lors du chargement de {parcelle} : {str(e)}")
            continue

    # Combinaison des DataFrames
    final_df = pd.concat(all_dfs) if all_dfs else pd.DataFrame()

    # Nettoyage final
    if not final_df.empty:
        # Suppression de la géométrie si GeoDataFrame
        if 'geometry' in final_df.columns:
            final_df = final_df.drop(columns='geometry')

        # Réorganisation des colonnes
        cols = ['Country', 'Parcelle'] + [c for c in final_df.columns if c not in ['Country', 'Parcelle']]
        return final_df[cols]

    return final_df


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


def predict_elasticnet(model, pred_data, mode):
    # Conversion selon le mode
    if mode == 'points':
        X_pred = pd.DataFrame([{
            'lat': p['lat'],
            'lon': p['lon'],
            **p['data']
        } for p in pred_data['points']])
    else:
        X_pred = load_filtered_data(
            parcelles=pred_data['parcelles'],
            dates=pred_data['dates'],
            rendement_min=0,
            rendement_max=10000,
            indice_min=0,
            indice_max=1,
            indice_name=pred_data['indice']
        )[model['features']]

    # Prédiction
    predictions = model['pipeline'].predict(X_pred)

    return {
        'predictions': predictions.tolist(),
        'stats': {
            'mean': float(np.mean(predictions)),
            'std': float(np.std(predictions)),
            'min': float(np.min(predictions)),
            'max': float(np.max(predictions))
        }
    }

def predict_elasticnet(model_dict, X_new):
    X_scaled = model_dict['scaler'].transform(X_new)
    return model_dict['model'].predict(X_scaled)
