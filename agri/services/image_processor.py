# services/image_processor.py
import rasterio
import numpy as np
import os
from django.conf import settings
from PIL import Image
from django.core.serializers.json import DjangoJSONEncoder
import json
import hashlib
from uuid import uuid4
import secrets
import time
import tifffile
from datetime import datetime

import plotly.graph_objects as go


class ParcelImageProcessor:
    def __init__(self, date, gridcolumnsize, gridrowsize, parcel_path):
        self.date = date
        self.parcel_path = parcel_path
        self.image_path = os.path.join(
            settings.STATIC_ROOT,
            'satellite_data',
            parcel_path,
            '12bands',
            f'{date}_S2A-12band.TIFF'
        )
        self.gridrowsize = gridrowsize
        self.gridcolumnsize = gridcolumnsize
        with rasterio.open(self.image_path) as src:
            self.bands = src.read()
            # Extraction des bandes RGB (4=Rouge, 3=Vert, 2=Bleu)
            self.red = self.bands[3]  # Bande 4
            self.green = self.bands[2]  # Bande 3
            self.blue = self.bands[1]  # Bande 2

            # Normalisation des bandes
            self.rgb = self.create_rgb_image()

    def generate_cell_id(self, x, y, gridrowsize, gridcolumnsize):
        # Seed aléatoire cryptographique
        random_seed = secrets.token_hex(8)  # 16 caractères hexadécimaux

        # Timestamp haute précision
        timestamp = str(time.time_ns())  # Précision nanoseconde

        # Combinaison multi-source
        base_id = f"{x}-{y}-{gridrowsize}-{gridcolumnsize}-{random_seed}-{timestamp}"

        # Hashage avec sel dynamique
        unique_hash = hashlib.sha3_256(f"{base_id}{os.urandom(16)}".encode()).hexdigest()[:16]

        # Combinaison aléatoire finale
        crypto_rand = secrets.token_bytes(4).hex()
        uuid_part = uuid4().hex[:6]

        return f"{unique_hash}-{crypto_rand}-{uuid_part}"

    def create_rgb_image(self):
        """Crée une image RGB normalisée"""
        # Normalisation globale sur les 3 bandes
        all_values = np.concatenate([self.red.flatten(), self.green.flatten(), self.blue.flatten()])
        min_val = np.percentile(all_values, 2)  # Utiliser le 2e percentile pour éviter les valeurs extrêmes
        max_val = np.percentile(all_values, 98)  # Utiliser le 98e percentile

        # Appliquer la même normalisation aux trois bandes
        red = np.clip(((self.red - min_val) / (max_val - min_val) * 255), 0, 255)
        green = np.clip(((self.green - min_val) / (max_val - min_val) * 255), 0, 255)
        blue = np.clip(((self.blue - min_val) / (max_val - min_val) * 255), 0, 255)

        return np.dstack((red.astype(np.uint8),
                          green.astype(np.uint8),
                          blue.astype(np.uint8)))

    def save_rgb_image(self):
        """Sauvegarde l'image RGB au format JPEG"""
        output_dir = os.path.join(settings.STATICFILES_DIRS[1], 'satellite_data', self.parcel_path, 'rgb_output')
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f'{self.date}_rgb.jpg')
        Image.fromarray(self.rgb).save(output_path)
        # Utiliser os.path pour obtenir le chemin relatif
        relative_path = os.path.relpath(output_path, settings.STATICFILES_DIRS[1])
        # Normaliser les séparateurs de chemin
        relative_path = os.path.normpath(relative_path)

        return relative_path

    def create_pixel_grid(self, band_index=1):
        """Crée une grille de zones de 4x4 pixels avec ID unique"""
        self.current_band = self.bands[band_index]
        height, width = self.current_band.shape
        grid = []
        for y in range(0, height, self.gridrowsize):
            for x in range(0, width, self.gridcolumnsize):
                cell_id = self.generate_cell_id( x, y, self.gridrowsize, self.gridcolumnsize)

                mean_val = float(np.mean(self.current_band[y:y + self.gridrowsize, x:x + self.gridcolumnsize]))
                mean_val = 0.0 if np.isnan(mean_val) or np.isinf(mean_val) else round(mean_val, 6)

                grid.append({
                    "id": cell_id,  # ID unique ajouté ici
                    "coordinates": [x, y, x + self.gridcolumnsize, y + self.gridrowsize],
                    "mean_value": mean_val
                })

        return grid

    @staticmethod
    def serialize_grid(grid: list) -> str:
        """Sérialise sans altérer l'ordre naturel"""
        # Vérification des IDs uniques
        seen = set()
        if any((id := item['id']) in seen or seen.add(id) for item in grid):  # noqa: E731
            raise ValueError("IDs dupliqués détectés")

        return json.dumps(
            grid,  # Pas de tri - conservation de l'ordre original
            cls=DjangoJSONEncoder,
            ensure_ascii=False,
            allow_nan=False
        )

    def get_grid_ids_and_data(self, raw_grid):
        """Retourne les IDs + données brutes formatées pour la session"""

        return {
            'ids': [cell['id'] for cell in raw_grid],
            'data': {
                cell['id']: {
                    'coordinates': cell['coordinates'],
                    'mean': cell['mean_value']
                } for cell in raw_grid
            }
        }

    def get_zone_data(self, datacell):
        x = datacell['coordinates'][0]
        y = datacell['coordinates'][1]

        grid_x = (x // self.gridcolumnsize) * self.gridcolumnsize
        grid_y = (y // self.gridrowsize) * self.gridrowsize

        return {
            'coordinates': [
                grid_x,
                grid_y,
                grid_x + self.gridcolumnsize,
                grid_y + self.gridrowsize
            ],
            'bands': {
                'band_1': round(
                    np.mean(self.bands[0, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_2': round(
                    np.mean(self.bands[1, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_3': round(
                    np.mean(self.bands[2, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_4': round(
                    np.mean(self.bands[3, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_5': round(
                    np.mean(self.bands[4, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_6': round(
                    np.mean(self.bands[5, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_7': round(
                    np.mean(self.bands[6, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_8': round(
                    np.mean(self.bands[7, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_8a': round(
                    np.mean(self.bands[8, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_9': round(
                    np.mean(self.bands[9, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_10': round(
                    np.mean(self.bands[10, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_11': round(
                    np.mean(self.bands[11, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2),
                'band_12': round(
                    np.mean(self.bands[12, grid_y:grid_y + self.gridrowsize, grid_x:grid_x + self.gridcolumnsize]), 2)
            }
        }



