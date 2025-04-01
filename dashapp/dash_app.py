import glob
import os
from datetime import datetime
import json
import re
import dash
from dash import Dash, html, dcc, Input, Output, callback, State
import plotly.express as px
import pandas as pd
import time
from shapely.geometry import Point
import plotly.graph_objects as go
import geopandas as gpd
import logging
import io
import base64
from dash import no_update  # Importez no_update
from PIL import Image
import matplotlib.pyplot as pl
from django_plotly_dash import DjangoDash  # Remplacez Dash par DjangoDash
from . import settings
from django.core.cache import cache
from .ElasticNet_models import predict_elasticnet, train_elasticnet_model, create_3d_feature_space  # Module personnalisé
import joblib  # Ajouter cet import en haut du fichier
from sklearn.metrics import r2_score
import numpy as np
import requests
import json
from django.middleware.csrf import get_token
import uuid

app = DjangoDash('ParcelleAnalysis')  # Nom unique pour l'application
# Fonction pour générer un ID de session
def generate_session_id():
    return str(uuid.uuid4())

# Dictionnaire global pour stocker les DataFrames chargés
dataframes_cache = {}
# Ajouter un timestamp pour suivre le temps d'exécution
print(f"[{time.time()}] Démarrage de l'application")

# Définir le chemin de base où sont stockées les données des parcelles
BASE_PATH = os.path.join(os.getcwd(),'dashapp','saved_parcelle_for_dash')
LISTE_DATES = getattr(settings, 'DASH_CONFIG', {}).get('LISTE_DATES', [])
LISTE_DATES_BOULINSARD = getattr(settings, 'DASH_CONFIG', {}).get('LISTE_DATES_BOULINSARD', [])
# Liste des parcelles disponibles
COUNTRIES = getattr(settings, 'DASH_CONFIG', {}).get('COUNTRIES', {})

dates_visees = pd.read_pickle(os.path.join(BASE_PATH,'dates_visee.pkl'))




def get_dataframe(country_code, parcelle):
    """Retourne le DataFrame correspondant au code pays et à la parcelle."""
    key = f"{country_code}/{parcelle}"

    # Vérifier si le DataFrame est déjà chargé dans le cache
    if key in dataframes_cache:
        return dataframes_cache[key]

    # Charger les données si elles ne sont pas en cache
    _, plot_df_filtered, _, _ = load_parcelle_data(country_code, parcelle)
    if plot_df_filtered is not None:
        dataframes_cache[key] = plot_df_filtered  # Ajouter au cache
        return plot_df_filtered

    return None  # Retourner None si les données ne peuvent pas être chargées

def add_to_cache(country_code, parcelle, dataframe):
    key = f"{country_code}/{parcelle}"
    dataframes_cache[key] = dataframe

def get_dates_for_country(all_dates, country_code):
    """Filtre les dates correspondant au code pays"""
    country_dates = all_dates[(all_dates['code_pays_1'] == country_code) |
                              (all_dates['code_pays_2'] == country_code)]
    return country_dates['dates'].tolist()

def get_available_parcelles(country_code):
    country_path = os.path.join(BASE_PATH, country_code)
    if not os.path.exists(country_path):
        return []

    # Obtenir tous les éléments et filtrer pour ne garder que les dossiers
    parcelles = [item for item in os.listdir(country_path)
                 if os.path.isdir(os.path.join(country_path, item))]
    print('parcelles',parcelles)
    parcelles.sort()
    return parcelles

def get_available_dates(country_code, parcelle):

    parcelle_path = os.path.join(BASE_PATH, str(country_code), str(parcelle))
    if not os.path.exists(parcelle_path):
        print("parcelle path n'existe pas.")
        return []

    encoded_files = glob.glob(os.path.join(parcelle_path, f"{str(parcelle)}_*_*_*_encodee.txt"))
    dates_with_idx = []
    for file in encoded_files:
        try:
            filename = os.path.basename(file)
            idx = int(re.search(r'\d+',filename.split('_')[2]).group())
            print('idx',idx)
            date_str = filename.split('_')[4]
            dates_with_idx.append((idx, date_str))
        except:
            try:
                filename = os.path.basename(file)
                # Extraction de la date (deuxième élément après le split)
                parts = filename.split('_')
                if len(parts) >= 5:
                    idx = int(re.search(r'\d+', parts[2]).group())# Vérifier qu'il y a au moins 3 parties
                    date_str = parts[4]
                    # Vérifier que c'est bien une date
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        dates_with_idx.append((idx, date_str))
            except Exception as e:
                print(f"Erreur lors de l'extraction de la date de {file}: {e}")
    # Trier par idx
    dates_with_idx.sort(key=lambda x: x[0])

    # Extraire uniquement les dates triées
    sorted_dates = [date for _, date in dates_with_idx]

    print('Dates triées par idx:', sorted_dates)
    return sorted_dates

# Fonction pour charger les données d'une parcelle
def load_parcelle_data(country_code, parcelle):
    print('country code', country_code)
    print('parcelle', parcelle)
    utils_path = os.path.join(BASE_PATH, str(country_code), str(parcelle), 'utils')

    # Vérifier si le dossier utils existe
    if not os.path.exists(utils_path):
        print(f"Le dossier utils pour la parcelle {parcelle} n'existe pas.")
        return None, None, None, None


    # Chemins des fichiers
    val_for_next_path = os.path.join(utils_path, f"{parcelle}_ValForNext.pkl")
    plot_df_filtered_path = os.path.join(utils_path, f"{parcelle}_filtered.pkl")

    # Vérifier si les fichiers existent
    if not os.path.exists(val_for_next_path) or not os.path.exists(plot_df_filtered_path):
        print(f"Fichiers manquants pour la parcelle {parcelle}.")
        return None, None, None, None


    # Charger les données
    try:
        val_for_next = pd.read_pickle(val_for_next_path)
        plot_df_filtered = pd.read_pickle(plot_df_filtered_path)

        print(f"Données chargées pour la parcelle {parcelle}")
        print(f"Dimensions de val_for_next: {val_for_next.shape}")
        print(f"Dimensions de plot_df_filtered: {plot_df_filtered.shape}")

        return val_for_next, plot_df_filtered, country_code, parcelle
    except Exception as e:
        print(f"Erreur lors du chargement des données pour la parcelle {parcelle}: {e}")
        return None, None, None, None

print("Création de la figure de base...")


# Fonction pour charger l'image encodée pour une parcelle et une date
def load_encoded_image(country_code, parcelle, date, date_visee, date_reelle):
    if str(parcelle) == 'Boulinsard':
        image_path = os.path.join(BASE_PATH, str(country_code), str(parcelle),
                                  f"{str(parcelle)}_{str(date)}_encodee.txt")
        if not os.path.exists(image_path):
            print(f"Image non trouvée pour {parcelle} à la date {date}")
            return None

        try:
            with open(image_path, 'r') as f:
                encoded_image = f.read()
            return encoded_image
        except Exception as e:
            print(f"Erreur lors du chargement de l'image pour {parcelle} à la date {date}: {e}")
            return None
    else:
        image_path = os.path.join(BASE_PATH, str(country_code), str(parcelle), f"{str(parcelle)}_X{str(date)}X_{str(date_visee)}_{str(date_reelle)}_encodee.txt")
        if not os.path.exists(image_path):
            print(f"Image non trouvée pour {parcelle} à la date {date}")
            return None

        try:
            with open(image_path, 'r') as f:
                encoded_image = f.read()
            return encoded_image
        except Exception as e:
            print(f"Erreur lors du chargement de l'image pour {parcelle} à la date {date}: {e}")
            return None


# Pré-calculer les GeoDataFrames projetés (une fois)
def get_projected_dataframe(country_code, parcelle):
    key = f"{country_code}/{parcelle}"
    if key not in dataframes_cache:
        return None

    gdf = dataframes_cache[key]

    # Projection en CRS métrique (ex: UTM zone appropriée)
    if gdf.crs is None or gdf.crs.to_epsg() != 32631:  # Exemple pour UTM 31N
        gdf = gdf.to_crs(epsg=32631)
        dataframes_cache[f"{key}_projected"] = gdf  # Cache séparé

    return gdf

def create_base_figure(selected_parcelle=None, selected_date=None, selected_index=None,
                       lat_min=48.0, lat_max=49.0, lon_min=5.0, lon_max=6.0,
                       zoom=12, center=None):
    # Création de la figure de base
    fig = go.Figure()

    # Configuration de base de la carte
    fig.update_layout(
        dragmode='lasso' if selected_parcelle else 'zoom',
        clickmode='event+select',
        margin=dict(r=0, t=0, l=0, b=0),
        map=dict(
            style="open-street-map",
            zoom=zoom,
            center=center if center else {'lat': (lat_min + lat_max) / 2, 'lon': (lon_min + lon_max) / 2},
            bounds=dict(
                west=-4.5,   # Brest (France)
                east=28.2,   # Est de l'Estonie
                south=45.4,  # Sud de la Slovénie
                north=59.5   # Nord de l'Estonie
            )
        )
    )

    return fig

def create_prediction_map(predictions):
    return {
        'data': [{
            'type': 'scattermap',
            'lat': [p['lat'] for p in predictions],
            'lon': [p['lon'] for p in predictions],
            'text': [f"Prédiction: {p['yield']:.2f} t/ha" for p in predictions],
            'marker': {'size': 12, 'color': 'purple'}
        }],
        'layout': {'map': {'style': 'carto-positron', 'zoom': 12}}
    }

def plot_feature_importance(model, features):
    return {
        'data': [go.Bar(x=features, y=model.feature_importances_)],
        'layout': {'title': 'Importance des Variables'}
    }

def create_3d_surface_plot(predictions):
    return {
        'data': [go.Surface(z=predictions)],
        'layout': {
            'scene': {
                'xaxis': {'title': 'Longitude'},
                'yaxis': {'title': 'Latitude'},
                'zaxis': {'title': 'Rendement'}
            }
        }
    }


def add_prediction_layer(fig, pred_data):
    try:
        fig.add_trace(
            go.Scattermap(
                lat=pred_data['lat'],
                lon=pred_data['lon'],
                mode='markers',
                marker=dict(
                    size=58,
                    color=pred_data['value'],
                    colorscale='Viridis',
                    opacity=0.7
                ),
                name='Prédictions'
            )
        )
    except KeyError as e:
        print(f"Erreur de format des prédictions : {str(e)}")

    return fig

def create_trace(plot_df, color_col, name, country_code, parcelle, default_size=15, default_colorscale='Viridis', hover_text=False):
    plot_df = gpd.GeoDataFrame(
        plot_df,
        geometry=gpd.points_from_xy(plot_df['Longitude'], plot_df['Latitude']),
        crs="EPSG:4326"  # WGS84
    )
    trace = go.Scattermap(
        lat=plot_df['Latitude'] if 'Latitude' in plot_df.columns else plot_df.geometry.y,
        lon=plot_df['Longitude'] if 'Longitude' in plot_df.columns else plot_df.geometry.x,
        mode='markers',
        marker=dict(
            size=default_size,
            color=plot_df[color_col],
            colorscale=default_colorscale,
            showscale=True,
            opacity=1
        ),
        customdata=np.stack([
            np.full(len(plot_df), country_code),
            np.full(len(plot_df), parcelle),
            np.full(len(plot_df), f"{country_code}/{parcelle}"),
            plot_df['Latitude'],
            plot_df['Longitude'],
            plot_df[color_col]
        ], axis=-1),
        hovertext=plot_df.apply(
            lambda x: (
                f"<b>{country_code}/{parcelle}</b><br>"
                f"Lat: {x['Latitude']:.4f}<br>"
                f"Lon: {x['Longitude']:.4f}<br>"
                f"{color_col}: {x[color_col]:.2f}"
            ) if hover_text else "",
            axis=1
        ),
        hoverinfo='text' if hover_text else 'skip',  # Désactive le hover info si hover_text=False
        name=name
    )
    return trace, plot_df

default_zoom = 12
# Initialiser avec une figure vide



# Charger les données pour Boulinsard
default_country = 'France'
default_country_code  = COUNTRIES[default_country]
parcelles_disponibles = get_available_parcelles(COUNTRIES[default_country])

liste_dates_visees_pour_le_pays = get_dates_for_country(dates_visees, default_country_code)

default_parcelle = 'Boulinsard'
dates_disponibles = get_available_dates(default_country_code, default_parcelle)
default_visee_date = liste_dates_visees_pour_le_pays[0] if liste_dates_visees_pour_le_pays else None
default_reelle_date = dates_disponibles[0] if dates_disponibles else None
default_date = LISTE_DATES_BOULINSARD[0] if LISTE_DATES_BOULINSARD else None

# Charger les données

utils_path = os.path.join(BASE_PATH, default_country_code, default_parcelle, 'utils')
val_for_next_path = os.path.join(utils_path, f"{default_parcelle}_ValForNext.pkl")
plot_df_filtered_path = os.path.join(utils_path, f"{default_parcelle}_filtered.pkl")

val_for_next = pd.read_pickle(val_for_next_path)
plot_df_filtered = pd.read_pickle(plot_df_filtered_path)

lat_max = val_for_next.at[0, 'ImpVal']
lat_min = val_for_next.at[1, 'ImpVal']
lon_min = val_for_next.at[2, 'ImpVal']
lon_max = val_for_next.at[3, 'ImpVal']
# Charger les indices disponibles depuis val_for_next
indices = val_for_next['NomIndice'].dropna().tolist()

print('indices',indices)

indices = [idx for idx in indices if idx]  # Supprimer les valeurs vides
default_index = 'NDVI' if 'NDVI' in indices else (indices[0] if indices else None)
# Filtrer les données pour la date sélectionnée si c'est un multi-index
if isinstance(plot_df_filtered.index, pd.MultiIndex) and 'date' in plot_df_filtered.index.names:
    if default_date in plot_df_filtered.index.get_level_values('date'):
        plot_df_date = plot_df_filtered.xs(default_date, level='date')
    else:
        plot_df_date = plot_df_filtered
else:
    plot_df_date = plot_df_filtered

print('plot_df_date',plot_df_date)

# Charger l'image encodée
if default_parcelle != 'Boulinsard':
    encoded_image_path = os.path.join(BASE_PATH, default_country_code, default_parcelle, f"{default_parcelle}_X{default_date}X_{default_visee_date}_{default_reelle_date}_encodee.txt")
else:
    encoded_image_path = os.path.join(BASE_PATH, default_country_code, default_parcelle,
                                      f"{str(default_parcelle)}_{default_date}_encodee.txt")
encoded_image = None
if os.path.exists(encoded_image_path):
    with open(encoded_image_path, 'r') as f:
        encoded_image = f.read()


base_fig = create_base_figure(selected_parcelle = default_parcelle)
val_for_next, plot_df_filtered, parcelle, country_code = load_parcelle_data(default_country_code, default_parcelle)
# Ajouter l'image de fond si disponible
if encoded_image:
    # Configuration avec l'image (MISE À JOUR pour MapLibre)
    base_fig.update_layout(
        map_style="open-street-map",  # Changé de mapbox_style
        map=dict(  # Changé de mapbox
            center=dict(lat=(lat_min + lat_max) / 2, lon=(lon_min + lon_max) / 2),
            zoom=default_zoom,
            layers=[
                {
                    "below": "traces",
                    "sourcetype": "image",
                    "source": f"data:image/png;base64,{encoded_image}",
                    "coordinates": [
                        [lon_min, lat_max],
                        [lon_max, lat_max],
                        [lon_max, lat_min],
                        [lon_min, lat_min]
                    ]
                }
            ]
        )
    )

ndvi_trace, ndvi_dataframe = create_trace(
    country_code=country_code,
    parcelle=parcelle,
    plot_df=plot_df_date,
    color_col='NDVI',
    name='NDVI',
    default_colorscale='Plasma'
)

rendement_trace, rendement_dataframe = create_trace(
    country_code=country_code,
    parcelle=parcelle,
    plot_df=plot_df_date,
    color_col='Rendement',
    name='Rendement',
    hover_text = True
)
add_to_cache(country_code, parcelle, rendement_dataframe)


# 5. Ajout des traces à la figure
base_fig.add_trace(ndvi_trace)
base_fig.add_trace(rendement_trace)

# 6. Finaliser la mise en page
base_fig.update_layout(
    title=f'Parcelle: {default_parcelle}, Date: {default_date}, Index:NDVI',
    margin=dict(l=0, r=0, t=30, b=0)
)


# Layout complet de l'application avec le dropdown d'indices corrigé
app.layout = html.Div([
    html.H1('Analyse des Parcelles Agricoles'),

    # Première ligne - Sélecteurs principaux
    html.Div([
        # Colonne 1 - Sélection de parcelle
        html.Div([
            html.Label('Pays:'),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': k, 'value': v} for k, v in COUNTRIES.items()],
                value=default_country_code,
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding-right': '20px'}),
        dcc.Store(id='parcelle-options-store',
                  storage_type='session'),
        # Colonne 2 - Sélection de parcelle
        html.Div([
            html.Label('Parcelle:'),
            dcc.Dropdown(
                id='parcelle-dropdown',
                options=[{'label': d, 'value': d} for d in parcelles_disponibles] if parcelles_disponibles else [
                    {'label': 'Pas de parcelles disponibles', 'value': 'no_parcelle'}],
                value=default_parcelle if default_parcelle else 'no_default_parcelle'
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding-left': '20px'}),

        # Colonne 3 - Sélection de date
        html.Div([
            html.Label('Date:'),
            dcc.Dropdown(
                id='date-dropdown',
                options=[{'label': d, 'value': d} for d in LISTE_DATES_BOULINSARD] if LISTE_DATES_BOULINSARD else [
                    {'label': 'Pas de date disponible', 'value': 'no_date'}],
                value=default_date if default_date else 'no_date'
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding-left': '20px'}),

        # Colonne 4 - Sélection d'indice (CORRIGÉ)
        html.Div([
            html.Label('Indice de végétation:'),
            dcc.Dropdown(
                id='index-dropdown',
                options=[{'label': idx, 'value': idx} for idx in indices] if indices else [
                    {'label': 'Pas d\'indice disponible', 'value': 'no_index'}],
                value=default_index if default_index else 'no_index'
            )
        ], style={'width': '18%', 'display': 'inline-block', 'padding-left': '20px'})
    ], style={'margin-bottom': '20px'}),

    # Deuxième ligne - Parcelles additionnelles
    html.Div([
        html.Label('Parcelles additionnelles à afficher:'),
        dcc.Checklist(id='parcelles-additionnelles',
                      options=[{'label': p, 'value': p} for p in parcelles_disponibles if p != default_parcelle],
                      value=[], inline=True, labelStyle={'margin-right': '15px'})
    ], style={'margin-bottom': '20px'}),

    # Nouvelle section Machine Learning
    html.Div([
        html.H3("Configuration du Modèle Prédictif"),
        html.Div([
            html.Label("Type de modèle:"),
            dcc.Dropdown(id='model-type', options=[
                {'label': 'Classification - Forêt Aléatoire', 'value': 'rf_class'},
                {'label': 'Classification - SVM', 'value': 'svm_class'},
                {'label': 'Régression - Gradient Boosting', 'value': 'gbr_reg'},
                {'label': 'Régression - Réseau de Neurones', 'value': 'nn_reg'},
                {'label': 'Régression - ElasticNet', 'value': 'elasticnet_reg'}
            ], value='elasticnet_reg')
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.H4("Sélection des données d'entraînement"),
        # Ajouter ces composants dans la section Machine Learning
        html.Div([
            dcc.RadioItems(
                id='prediction-mode',
                options=[
                    {'label': 'Sélection manuelle par points', 'value': 'points'},
                    {'label': 'Filtrage automatique', 'value': 'filter'}
                ],
                value='points'
            ),

            # Div pour le mode "points"
            html.Div([
                html.Button("Ajouter points d'entraînement", id='add-train-points-btn'),
                html.Button("Voir points d'entraînement", id='view-train-points-btn'),
                html.Div("Points séléctionnés pour l'entrainement", id='selections-display'),
                html.Button("Ajouter points de prédiction", id='add-pred-points-btn'),
                html.Button("Voir points de prédiction", id='view-pred-points-btn'),
            ], id='points-mode-div', style={'display':'block'}),

            # Div pour le mode "filter"
            html.Div([
                # Contenu existant pour la sélection des parcelles et les filtres
            html.H4("Filtres des données"),

            # Sélection des parcelles
            html.Div([
                html.Label("Sélectionner les parcelles :"),
                dcc.Dropdown(
                    id='parcelles-selection',
                    options=[{'label': p, 'value': p} for p in parcelles_disponibles],
                    multi=True,
                    value=[default_parcelle]
                )
            ], style={'margin-bottom': '10px'}),
            html.Div([
                html.Div([
                    # Slider pour exclure les valeurs minimales (0-25%)
                    html.Label("Exclure les plus faibles:", style={'display': 'block'}),
                    dcc.Slider(
                        id='rendement-min-slider',
                        min=0,
                        max=25,
                        step=1,
                        marks={i: f'{i}%' for i in range(0, 26, 5)},
                        value=0,
                        tooltip={'placement': 'bottom', 'always_visible': False}
                        # Désactiver always_visible si nécessaire
                    ),

                    # Slider pour exclure les valeurs maximales (75-100%)
                    html.Label("Exclure les plus élevées:", style={'display': 'block', 'margin-top': '15px'}),
                    dcc.Slider(
                        id='rendement-max-slider',
                        min=75,
                        max=100,
                        step=1,
                        marks={i: f'{i}%' for i in range(75, 101, 5)},
                        value=100,
                        tooltip={'placement': 'bottom', 'always_visible': False}
                        # Désactiver always_visible si nécessaire
                    )
                ], style={'width': '45%', 'display': 'inline-block', 'vertical-align': 'top'}),

                html.Div([
                    # Slider pour exclure les valeurs minimales (0-25%)
                    html.Label("Exclure les plus faibles:", style={'display': 'block'}),
                    dcc.Slider(
                        id='indice-min-slider',
                        min=0,
                        max=25,
                        step=1,
                        marks={i: f'{i}%' for i in range(0, 26, 5)},
                        value=0,
                        tooltip={'placement': 'bottom', 'always_visible': False}  # Désactiver always_visible si nécessaire
                    ),

                    # Slider pour exclure les valeurs maximales (75-100%)
                    html.Label("Exclure les plus élevées:", style={'display': 'block', 'margin-top': '15px'}),
                    dcc.Slider(
                        id='indice-max-slider',
                        min=75,
                        max=100,
                        step=1,
                        marks={i: f'{i}%' for i in range(75, 101, 5)},
                        value=100,
                        tooltip={'placement': 'bottom', 'always_visible': False}  # Désactiver always_visible si nécessaire
                    )
                ], style={'width': '45%', 'display': 'inline-block', 'vertical-align': 'top'}),
            ],id='filter-mode-div', style = {'display' : 'none'}),
                # Affichage des valeurs actuelles
                html.Div(id='extremes-output', style={'margin-top': '20px'})
            ], style={'padding': '15px', 'border': '1px solid #eee'}),
            # Ajouter dans la section Machine Learning
            html.Div([
                html.H4("Configuration des prédictions"),

                # Configuration pour le mode filtre
                html.Div([
                    html.Div([
                        html.Label("Parcelles à prédire:"),
                        dcc.Dropdown(
                            id='pred-parcelles-selection',
                            options=[{'label': p, 'value': p} for p in parcelles_disponibles],
                            multi=True
                        )
                    ], style={'margin-bottom': '10px'}),
                ]),

                html.Div([
                    # Dropdown des indices
                    html.Div([
                        html.Label("Sélectionner les indices utilisées pour l'entrainement :"),
                        dcc.Dropdown(
                            id='indices-dropdown',
                            options=[{'label': idx, 'value': idx} for idx in indices],
                            multi=True,
                            value=['NDVI'],  # NDVI par défaut
                            placeholder="Choisissez un ou plusieurs indices"
                        )
                    ], style={'margin-bottom': '10px'}),

                html.Div([
                            html.H4("Configuration des dates utilisées"),

                            html.Div([
                                html.Label("Dates utilisées pour l'entrainement Boulinsard:"),
                                dcc.Dropdown(
                                    id='pred-dates-selection',
                                    options=[{'label': d, 'value': d} for d in LISTE_DATES_BOULINSARD],
                                    multi=True
                                )
                            ], style={'margin-bottom': '10px'}),
                            # Dropdown des dates
                            html.Div([
                                html.Label("Dates utilisées pour l'entrainement autres parcelles:"),
                                dcc.Dropdown(
                                    id='dates-selected-fo-training',
                                    options=[{'label': date, 'value': date} for date in LISTE_DATES],
                                    multi=True,
                                    value=[LISTE_DATES[0]] if LISTE_DATES else [],  # Date_1 par défaut
                                    placeholder="Choisissez une ou plusieurs dates"
                                )
                            ], style={'margin-bottom': '10px'})
                        ])
                        ], id='filter-mode-config')
                    ], style={'padding': '15px', 'border': '1px solid #eee'}),
        ]),
                html.Div([
                    html.Button("Lancer l'Entraînement", id='train-model-btn', n_clicks=0,
                                style={'background-color': '#4CAF50', 'margin-right': '10px'}),
                    html.Button("Exécuter les Prédictions", id='predict-btn', n_clicks=0, style={'background-color': '#008CBA'})
                ], style={'padding': '20px', 'border-top': '1px solid #ddd'}),

            html.Div([

                html.Div(id='training-result-output')
            ]),
        html.Div([
            dcc.Graph(id='map-graph', figure=base_fig, style={'height': '80vh'}),
            html.Div(id='model-results', style={'margin-top': '20px'}),
            dcc.Store(id='csrf_token'),
            dcc.Store(id='session-id-store', data=str(uuid.uuid4()), storage_type='session'),
            dcc.Store(id='csrf-token-store', data=''),
            dcc.Store(id='model-results-store'),
            dcc.Store(id='parcelle-options-store', storage_type='session'),
            dcc.Store(id='selected-points-store', data=[]),
            dcc.Store(id='training-points-store', data=[]),
            dcc.Store(id='training-dates-store', data=[]),
            dcc.Store(id='training-indices-store', data=[]),
            dcc.Store(id='prediction-points-store', data=[]),
            dcc.Store(id='prediction-data-store'),
            dcc.Store(id='training-data-store'),
            dcc.Store(id='map-view-state', storage_type='session',
                      data={"zoom": 12, "center": {"lat": (lat_min + lat_max) / 2, "lon": (lon_min + lon_max) / 2}}),
            dcc.Checklist(id='show-predictions', style={'display': 'none'})
        ], style={'padding': '20px'})
    ])
])

# Callback pour mettre à jour l'affichage des Divs
@app.callback(
    [Output('points-mode-div', 'style'),
     Output('filter-mode-div', 'style')],
    [Input('prediction-mode', 'value')]
)
def update_div_visibility(prediction_mode):
    if prediction_mode == 'points':
        # Afficher le Div "points" et cacher le Div "filter"
        return {'display': 'block'}, {'display': 'none'}
    elif prediction_mode == 'filter':
        # Afficher le Div "filter" et cacher le Div "points"
        return {'display': 'none'}, {'display': 'block'}
    else:
        # Par défaut, cacher les deux Divs (optionnel)
        return {'display': 'none'}, {'display': 'none'}

app.clientside_callback(
    """
    function(n) {
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
        }
        return getCookie('csrftoken');
    }
    """,
    Output('csrf-token-store', 'data'),
     Input('csrf_token', 'data') # Utilisez un composant qui existe dans votre layout
)



@app.callback(
    Output('parcelle-options-store', 'data'),
    Output('parcelle-dropdown', 'options'),
    Output('parcelle-dropdown', 'value'),
    Output('parcelles-additionnelles', 'options'),
    Output('parcelles-additionnelles', 'value'),
    Input('country-dropdown', 'value'),
    prevent_initial_call=True
)
def update_parcelles_options(selected_country):
    # Récupérer depuis le middleware
    parcelles = get_available_parcelles(selected_country)

    if not parcelles:
        return {}, [{'label': 'Pas de parcelle disponible', 'value': 'no_parcelle'}], 'no_parcelle', [], []

    options_parcelles = [{'label': parcelle, 'value': parcelle} for parcelle in parcelles]
    return {'parcelles': parcelles}, options_parcelles, parcelles[0], options_parcelles, []

# Callback pour mettre à jour la liste des dates en fonction de la parcelle sélectionnée
@app.callback(
    Output('date-dropdown', 'options'),
    Output('date-dropdown', 'value'),
    Output('index-dropdown', 'options'),
    Output('index-dropdown', 'value'),
    Input('parcelle-dropdown', 'value'),
    Input('country-dropdown', 'value'),
prevent_initial_call=True
)
def update_date_and_index_options(selected_parcelle, selected_country):
    val_for_next, _, country_code, parcelle = load_parcelle_data(selected_country, selected_parcelle )

    if val_for_next is None:
        return [{'label': 'Pas d\'indice disponible', 'value': 'no_index'}], 'no_index'

    indices = val_for_next['NomIndice'].dropna().tolist()
    indices = [idx for idx in indices if idx]  # Supprimer les valeurs vides

    if not indices:
        return [{'label': 'Pas d\'indice disponible', 'value': 'no_index'}], 'no_index'

    options_index = [{'label': idx, 'value': idx} for idx in indices]
    dates = LISTE_DATES
    liste_reelle_date = get_available_dates(selected_country, selected_parcelle)
    liste_vised_date = get_dates_for_country(dates_visees, selected_country)
    if not dates:
        return [{'label': 'Pas de date pour cette parcelle', 'value': 'no_date'}], 'no_date'

    options_date = [{'label': date, 'value': date} for date in dates]
    return options_date, dates[0], options_index, indices[0]  # Retourner le premier indice comme valeur par défaut  # Retourner la première date comme valeur par défaut


app.clientside_callback(
    """
    function(n_clicks, mode, dates_boulinsard, dates_normales, indices, points_store, 
             rendement_min, rendement_max, indice_min, indice_max, csrf_token) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }

        // Construction du payload
        const payload = {
            training: {
                mode: mode,
                dates: {
                    boulinsard: dates_boulinsard,
                    normales: dates_normales
                },
                indices: indices,
                filters: {}
            },
            country_code: "FR"
        };

        // Données spécifiques au mode
        if (mode === 'points') {
            payload.training.parcelles = points_store;
        } else {
            payload.training.filters = {
                rendement_min: rendement_min,
                rendement_max: rendement_max,
                indice_min: indice_min,
                indice_max: indice_max
            };
        }

        // Envoi de la requête
        return fetch('parcelles/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            return JSON.stringify(data);
        })
        .catch(error => {
            return `Erreur: ${error.message}`;
        });
    }
    """,
    Output('training-result-output', 'children'),  # Ajoutez un Div pour afficher les résultats
    [Input('train-model-btn', 'n_clicks')],
    [State('prediction-mode', 'value'),
     State('pred-dates-selection', 'value'),
     State('dates-selected-fo-training', 'value'),
     State('indices-dropdown', 'value'),
     State('training-points-store', 'data'),
     State('rendement-min-slider', 'value'),
     State('rendement-max-slider', 'value'),
     State('indice-min-slider', 'value'),
     State('indice-max-slider', 'value'),
     State('csrf-token-store', 'data')]
)

@app.callback(
    Output('map-view-state', 'data'),
    Input('map-graph', 'relayoutData'),
    State('map-view-state', 'data'),
    prevent_initial_call=True
)
def store_map_view(relayoutData, current_state):
    if relayoutData is None:
        return current_state

    new_state = current_state.copy()

    # Common MapLibre property names
    if 'map.zoom' in relayoutData:
        new_state['zoom'] = relayoutData['map.zoom']

    elif 'mapbox.zoom' in relayoutData:
        new_state['zoom'] = relayoutData['mapbox.zoom']

    # Additional variants to check
    elif 'zoom' in relayoutData:
        new_state['zoom'] = relayoutData['zoom']
    # Center coordinates
    if 'map.center' in relayoutData:
        new_state['center'] = relayoutData['map.center']

    elif 'mapbox.center' in relayoutData:
        new_state['center'] = relayoutData['mapbox.center']

    elif 'center' in relayoutData:
        new_state['center'] = relayoutData['center']
    return new_state


# Callback pour récupérer la sélection
# Callback de sélection modifié
@app.callback(
    Output('selected-points-store', 'data'),
    Input('map-graph', 'selectedData'),
    prevent_initial_call=True
)
def handle_selection(selectedData):
    if not selectedData:
        print("Aucun point sélectionné.")
        return []

    points = []
    for p in selectedData['points']:
        country_code = p['customdata'][0]
        parcelle = p['customdata'][1]
        lat = p['customdata'][3]
        lon = p['customdata'][4]

        # Accéder au cache pour récupérer le DataFrame correspondant
        key = f"{country_code}/{parcelle}"
        dataframe = dataframes_cache.get(key)

        if dataframe is not None:
            point_data = dataframe[
                (dataframe['Latitude'] == lat) &
                (dataframe['Longitude'] == lon)
            ]
            points.append({
                'country_code': country_code,
                'parcelle': parcelle,
                'lat': lat,
                'lon': lon,
                'value': p['customdata'][5],
                'data': point_data.to_dict('records')  # Inclure les données complètes du point
            })

    return points





# Fonction manquante 2: Génération du tableau de prédictions
def generate_prediction_table(predictions):
    """Crée un tableau HTML des résultats de prédiction"""
    return html.Table(
        # En-tête
        [html.Tr([html.Th("Zone"), html.Th("Rendement Prédit (t/ha)")])] +
        # Lignes de données
        [html.Tr([html.Td(i+1), html.Td(f"{pred:.2f}")])
         for i, pred in enumerate(predictions)],
        style={'margin-top': '20px'}
    )


@app.callback(
    Output('training-points-store', 'data'),
    Input('add-train-points-btn', 'n_clicks'),
    [State('selected-points-store', 'data'),
     State('training-points-store', 'data'),
     State('session-id-store', 'data'),
     State('csrf-token-store', 'data')],
    prevent_initial_call=True
)
def add_training_points(n_clicks, selected_points, clean_existing_training_points, session_id, csrf_token):
    if not selected_points:
        return dash.no_update

    # Appel API pour enregistrer les points en base
    try:
        response = requests.post(
            '/api/save-points/',
            json={
                'session_id': session_id,
                'points': selected_points
            },
            headers={
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token
            }
        )

        if response.status_code == 200:
            # Traitement des points comme avant
            new_training_point = []
        for point in selected_points:
            country_code = point['country_code']
            parcelle = point['parcelle']
            lat = float(point['lat'])  # Conversion en float
            lon = float(point['lon'])  # Conversion en float

            # Charger le DataFrame correspondant
            plot_df = get_dataframe(country_code, parcelle)
            # Batch processing pour tous les points
            all_points = [
                (Point(float(p['lon']), float(p['lat'])), p)
                for p in selected_points
            ]

            # Conversion en GeoSeries projetée
            search_points = gpd.GeoSeries(
                [p[0] for p in all_points],
                crs="EPSG:4326"
            ).to_crs(epsg=32631).buffer(4)  # 10 mètres


        clean_training_points = clean_existing_training_points or []
        for point in new_training_point:
            # Conversion des types et nettoyage des données
            clean_point = {
                'country_code': str(point['country_code']),
                'parcelle': str(point['parcelle']),
                'lat': float(point['lat']),
                'lon': float(point['lon']),
                'value': float(point['value']),
                'data': {
                    'Latitude': float(point['data']['Latitude']),
                    'Longitude': float(point['data']['Longitude']),
                    'Rendement': float(point['data']['Rendement']),
                    'NDVI': float(point['data']['NDVI']) if point['data']['NDVI'] else None,
                    'geometry': f"POINT ({point['data']['Longitude']} {point['data']['Latitude']})"  # WKT
                }
            }

            # Conversion des NaN/None
            for k, v in clean_point['data'].items():
                if v is None:
                    clean_point['data'][k] = 'N/A'

            clean_training_points.append(clean_point)
        print('clean training points:', clean_training_points[:10])
        if not selected_points:

            return clean_training_points
        else:
            print(f"Erreur API: {response.text}")
            return clean_existing_training_points

    except Exception as e:
        print(f"Exception: {str(e)}")
        return clean_existing_training_points


@app.callback(
    Output('selections-display', 'children'),
    [Input('view-train-points-btn', 'n_clicks')],
    [State('session-id-store', 'data'),
     State('parcelle-dropdown', 'value'),
     State('country-dropdown', 'value'),
     State('indices-dropdown', 'value')],
    prevent_initial_call=True
)
def display_saved_points(n_clicks, session_id, parcelle, country, indices):
    if not n_clicks:
        return dash.no_update

    try:
        # Appel à l'API pour récupérer les points sauvegardés
        response = requests.get(
            f'/api/get-points/?session_id={session_id}&country={country}&parcelle={parcelle}'
        )

        if response.status_code == 200:
            data = response.json()
            points = data.get('points', [])

            if not points:
                return html.Div("Aucun point sauvegardé trouvé")

            # Limiter à 5 points pour l'affichage
            sample_points = points[:5]

            return html.Div([
                html.H4(f"Points sauvegardés ({parcelle})"),
                html.Table([
                               html.Tr(
                                   [html.Th("Latitude"), html.Th("Longitude"), html.Th("Rendement"), html.Th("NDVI")])
                           ] + [
                               html.Tr([
                                   html.Td(f"{p['latitude']:.4f}"),
                                   html.Td(f"{p['longitude']:.4f}"),
                                   html.Td(f"{p['rendement']:.2f}" if p['rendement'] else "N/A"),
                                   html.Td(f"{p['ndvi']:.4f}" if p['ndvi'] else "N/A")
                               ]) for p in sample_points
                           ])
            ])
        else:
            return html.Div(f"Erreur lors de la récupération des points: {response.text}")

    except Exception as e:
        return html.Div(f"Erreur: {str(e)}")



# Callback pour mettre à jour la carte avec plusieurs parcelles
@app.callback(
    Output('map-graph', 'figure'),
    Input('parcelle-options-store', 'data'),
    Input('parcelle-dropdown', 'value'),
    Input('date-dropdown', 'value'),
    Input('index-dropdown', 'value'),
    Input('prediction-data-store', 'data'),  # Move this Input before any States
    State('country-dropdown', 'value'),
    State('parcelle-dropdown', 'value'),
    State('map-view-state', 'data'),
    State('show-predictions', 'value'),
    prevent_initial_call=True
)
def update_graph(parcelle_options, selected_parcelle, selected_date, selected_index, prediction_data, selected_country, parcelles_additionnelles, map_state, show_predictions):

    val_for_next, plot_df_filtered, country_code, parcelle = load_parcelle_data(selected_country, selected_parcelle)
    print('plot_df_filtered',plot_df_filtered)
    lat_max = val_for_next.at[0, 'ImpVal']
    lat_min = val_for_next.at[1, 'ImpVal']
    lon_min = val_for_next.at[2, 'ImpVal']
    lon_max = val_for_next.at[3, 'ImpVal']
    # Récupérer l'état de la carte
    zoom = 12
    center = {"lat": (lat_min + lat_max) / 2, "lon": (lon_min + lon_max) / 2}
    # Vérifier si les valeurs sont valides
    if map_state:
        zoom = map_state.get('zoom', zoom)
        center = map_state.get('center', center)
        print("center get", center)

    if selected_date == 'no_date' or selected_index == 'no_index':
        no_fig_dict = create_base_figure(center=center,
                                           zoom=zoom)
        return create_base_figure(no_fig_dict)


    if val_for_next is None or plot_df_filtered is None:
        no_fig_dict = create_base_figure(center=center,
                                           zoom=zoom)
        return create_base_figure(no_fig_dict)


    # Filtrer par date si nécessaire
    if isinstance(plot_df_filtered.index, pd.MultiIndex) and 'date' in plot_df_filtered.index.names:
        if selected_date in plot_df_filtered.index.get_level_values('date'):
            date_df = plot_df_filtered.xs(selected_date, level='date')
        else:
            date_df = plot_df_filtered
    else:
        date_df = plot_df_filtered


    # Initialiser avec une figure vide
    base_fig_dict = create_base_figure(center=center,zoom=zoom)
    fig_new = go.Figure(base_fig_dict)
    # Ajout conditionnel des prédictions
    if prediction_data and not prediction_data.empty:
        fig_new = add_prediction_layer(fig_new, prediction_data)
    # Liste pour stocker les limites de toutes les parcelles
    all_lat_mins = [lat_min]
    all_lat_maxs = [lat_max]
    all_lon_mins = [lon_min]
    all_lon_maxs = [lon_max]

    dates = LISTE_DATES

    liste_reelle_date = get_available_dates(selected_country, selected_parcelle)
    liste_vised_date = get_dates_for_country(dates_visees, selected_country)
    # Vérification que les listes ont la même longueur

    if str(selected_parcelle) != 'Boulinsard':
        assert len(dates) == len(liste_vised_date) == len(liste_reelle_date), "Les listes doivent avoir la même longueur"

        # Création du DataFrame
        date_df = pd.DataFrame({
            'nom_date': dates,
            'date_visee': liste_vised_date,
            'date_reelle': liste_reelle_date
        })
        print('date_df',date_df)
        print('selected_date',selected_date)
        row_date = date_df.loc[date_df['nom_date'] == selected_date]
        selected_vised_date = row_date['date_visee'].values
        selected_reelle_date = row_date['date_reelle'].values
        selected_vised_date = selected_vised_date[0]
        selected_reelle_date = selected_reelle_date[0]

    else:
        selected_vised_date = None
        selected_reelle_date = None
    # 1. Ajouter l'image de la parcelle principale
    new_image = load_encoded_image(selected_country, selected_parcelle, selected_date, selected_vised_date, selected_reelle_date)

    fig_new.update_layout(
        map_style="open-street-map",
        map=dict(
            center=center,  # Centre calculé pour la parcelle actuelle
            zoom=zoom,  # Zoom préservé de l'état précédent
            layers=[
                {
                    "below": "traces",
                    "sourcetype": "image",
                    "source": f"data:image/png;base64,{new_image}",
                    "coordinates": [
                        [lon_min, lat_max],
                        [lon_max, lat_max],
                        [lon_max, lat_min],
                        [lon_min, lat_min]
                    ]
                }
            ]
        )
    )

    print('latitude',plot_df_filtered.xs(selected_date, level='date')['Latitude'])
    print('longitude',plot_df_filtered.xs(selected_date, level='date').index)
    print('selected_date',plot_df_filtered.xs(selected_date, level='date')[selected_index])
    # Filtrer les données pour la date sélectionnée si c'est un multi-index
    if isinstance(plot_df_filtered.index, pd.MultiIndex) and 'date' in plot_df_filtered.index.names:
        if default_date in plot_df_filtered.index.get_level_values('date'):
            plot_df_date = plot_df_filtered.xs(selected_date, level='date')
        else:
            plot_df_date = plot_df_filtered
    else:
        plot_df_date = plot_df_filtered
    index_trace, ndvi_dataframe = create_trace(
        country_code=country_code,
        parcelle=parcelle,
        plot_df=plot_df_date,
        color_col='NDVI',
        name='NDVI',
        default_colorscale='Plasma'
    )

    rendement_trace, rendement_dataframe = create_trace(
        country_code = country_code,
        parcelle = parcelle,
        plot_df=plot_df_date,
        color_col='Rendement',
        name='Rendement',
        hover_text = True
    )
    add_to_cache(country_code, parcelle, rendement_dataframe)
    fig_new.add_trace(index_trace)
    fig_new.add_trace(rendement_trace)

    for parcelle in parcelles_additionnelles:
        if parcelle == selected_parcelle:
            continue

        # Chargement des données
        add_val_for_next, add_plot_df, country_code, parcelle_num = load_parcelle_data(selected_country, parcelle)

        if add_val_for_next is None or add_plot_df is None:
            continue

        # Calcul des coordonnées
        lat_min = add_val_for_next.at[1, 'ImpVal']
        lat_max = add_val_for_next.at[0, 'ImpVal']
        lon_min = add_val_for_next.at[2, 'ImpVal']
        lon_max = add_val_for_next.at[3, 'ImpVal']

        # Ajout de l'image
        add_encoded_image =  load_encoded_image(selected_country, selected_parcelle, selected_date, selected_vised_date, selected_reelle_date)
        if add_encoded_image:
            fig_new.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{add_encoded_image}",
                    x=lon_min,
                    y=lat_max,
                    sizex=lon_max - lon_min,
                    sizey=lat_max - lat_min,
                    sizing="stretch",
                    opacity=0.5,
                    layer="below"
                )
            )
        # Filtrer les données pour la date sélectionnée si c'est un multi-index
        if isinstance(plot_df_filtered.index, pd.MultiIndex) and 'date' in plot_df_filtered.index.names:
            if default_date in plot_df_filtered.index.get_level_values('date'):
                add_plot_df_date = plot_df_filtered.xs(selected_date, level='date')
            else:
                add_plot_df_date = plot_df_filtered
        else:
            add_plot_df_date = plot_df_filtered
        # 3. Ajout des traces d'indice avec create_trace
        if selected_index in add_plot_df.columns:
            add_trace, trace_df = create_trace(
                country_code=country_code,
                parcelle=parcelle,
                plot_df=add_plot_df_date,
                color_col=selected_index,
                name=f"{parcelle} - {selected_index}",
                hover_text =  True
            )
            add_to_cache(country_code, parcelle, trace_df)

            fig_new.add_trace(add_trace)

    # Calculer les limites globales et ajuster le centre
    global_lat_min = min(all_lat_mins)
    global_lat_max = max(all_lat_maxs)
    global_lon_min = min(all_lon_mins)
    global_lon_max = max(all_lon_maxs)

    # 6. Finaliser la mise en page
    fig_new.update_layout(
        title=f'Parcelle: {selected_parcelle}, Date: {selected_date} Index {selected_index}',
        margin=dict(l=0, r=0, t=30, b=0)
    )

    return fig_new


