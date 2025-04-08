import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.neighbors import KDTree
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler
import pandas as pd
import geopandas as gpd
from typing import List, Tuple

class SpatioTemporalTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, time_window='30D', spatial_radius=500):
        self.time_window = time_window
        self.spatial_radius = spatial_radius

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return create_spatiotemporal_vectors(X, self.time_window, self.spatial_radius)


pipeline = Pipeline([
    ('st_transform', SpatioTemporalTransformer()),
    ('scaler', StandardScaler()),
    ('model', ElasticNet(alpha=0.5, l1_ratio=0.5))
])

# 1. Génération des valeurs aléatoires
def generer_valeurs_aleatoires(base_value, n=4):
    """Génère 4 valeurs autour d'une valeur de base avec fluctuation contrôlée"""
    return np.linspace(base_value*0.9, base_value*1.1, n) * np.random.normal(1, 0.05, n)



def create_spatiotemporal_vectors(point_data: pd.Series,
                                  neighbors_data: gpd.GeoDataFrame,
                                  dates: pd.DatetimeIndex) -> list:
    """
    Génère une liste de vecteurs 2D (jours, valeur_temperee) par date

    Args:
        point_data: Série avec valeurs temporelles du point central
        neighbors_data: GeoDataFrame des points voisins avec leurs séries temporelles
        dates: Liste complète des dates

    Returns:
        Liste de tuples (jours_depuis_debut, valeur_temperee)
    """
    # Calcul des jours depuis le début
    columns = point_data.index.tolist()

    # Filtrer les floats et integers
    numbers = [i for i in columns if isinstance(i, (int, float))]

    # Filtrer uniquement les digits (dans des chaînes de caractères)
    digits = [int(char) for item in columns if isinstance(item, str) for char in item if char.isdigit()]
    if len(numbers)==0:
        days = digits
    else:
        days = numbers

    # Calcul des poids spatiaux
    distances = neighbors_data.geometry.distance(point_data.geometry)
    weights = 1 / (1 + distances)
    weights /= weights.sum()

    vectors = []
    neighbors_data.columns = neighbors_data.columns.map(str)
    for i, day in enumerate(days):
        # Valeur du point central
        val_point = point_data[float(day)]

        # Valeur moyenne pondérée des voisins
        val_voisins = np.average(neighbors_data.loc[:, str(day)], weights=weights)

        # Combinaison tempérée (70% point + 30% voisins)
        val_temperee = 0.7 * val_point + 0.3 * val_voisins

        vectors.append((int(day), val_temperee))

    return vectors


def calcul_valeurs_combinees(centroid: float,
                             arrivee: float,
                             vecteurs: List[Tuple[float, float]]) -> float:
    """
    Calcule la valeur combinée en utilisant TOUS les vecteurs pour le centroïde

    Args:
        centroid: Jour cible du centroïde (ex: 50)
        arrivee: Jour cible d'arrivée (ex: 100)
        vecteurs: Liste de tuples (jour, valeur)

    Returns:
        Valeur combinée unique avec intégration totale des vecteurs
    """
    # 1. Calcul du centroïde comme moyenne pondérée de TOUS les vecteurs
    jours = np.array([v[0] for v in vecteurs])
    valeurs = np.array([v[1] for v in vecteurs])

    # Poids temporels inversement proportionnels à la distance au centroid théorique
    weights_centroid = 1 / (1 + np.abs(jours - centroid))
    weights_centroid /= weights_centroid.sum()

    valeur_centroid = np.average(valeurs, weights=weights_centroid)

    # 2. Calcul de la projection vers l'arrivée avec régression sur TOUS les vecteurs
    if len(vecteurs) < 2:
        return np.nan

    # Séparation avant/après centroid
    jours_post = [v[0] for v in vecteurs if v[0] >= centroid]
    valeurs_post = [v[1] for v in vecteurs if v[0] >= centroid]

    # Régression linéaire sur la période post-centroid
    if len(jours_post) >= 2:
        slope, intercept = np.polyfit(jours_post, valeurs_post, 1)
        valeur_arrivee = slope * arrivee + intercept
    else:
        valeur_arrivee = valeurs[-1] if len(valeurs) > 0 else 0

    # 3. Combinaison selon recherche agronomique
    return 0.6 * valeur_centroid + 0.4 * valeur_arrivee