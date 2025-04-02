from django.core.cache import cache
from django.conf import settings
from pathlib import Path
import pandas as pd
import os

BASE_PATH = Path(settings.BASE_DIR) / 'saved_parcelle_for_dash'


def load_parcelle_data(parcelle):
    """Charge les données brutes depuis le stockage"""
    parcelle_path = BASE_PATH / f"{parcelle}.csv"
    return pd.read_csv(parcelle_path, parse_dates=['date'])


def get_cached_parcelle_data(parcelle):
    """Version avec cache des données de parcelle"""
    cache_key = f'parcelle_{parcelle}_data'
    data = cache.get(cache_key)

    if not data:
        data = load_parcelle_data(parcelle)
        cache.set(cache_key, data, timeout=3600)  # Cache pour 1 heure
    return data
