# services/image_processor.py
import rasterio
import numpy as np
import os
from django.conf import settings
from PIL import Image
from django.core.serializers.json import DjangoJSONEncoder
import json




class ParcelImageProcessor:
    def __init__(self, date):
        self.date = date
        self.image_path = os.path.join(
            settings.STATIC_ROOT,
            'satellite_data',
            '12bands',
            f'{date}_S2A-12band.TIFF'
        )
        with rasterio.open(self.image_path) as src:
            self.bands = src.read()
            # Extraction des bandes RGB (4=Rouge, 3=Vert, 2=Bleu)
            self.red = self.bands[3]  # Bande 4
            self.green = self.bands[2]  # Bande 3
            self.blue = self.bands[1]  # Bande 2

            # Normalisation des bandes
            self.rgb = self.create_rgb_image()

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
        output_dir = os.path.join(settings.STATICFILES_DIRS[1], 'satellite_data', 'rgb_output')
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f'{self.date}_rgb.jpg')
        Image.fromarray(self.rgb).save(output_path)
        # Utiliser os.path pour obtenir le chemin relatif
        relative_path = os.path.relpath(output_path, settings.STATICFILES_DIRS[1])
        # Normaliser les séparateurs de chemin
        relative_path = os.path.normpath(relative_path)

        return relative_path

    def create_pixel_grid(self, band_index=1):
        """Crée une grille de zones de 4x4 pixels pour la bande spécifiée"""
        self.current_band = self.bands[band_index]
        height, width = self.current_band.shape
        grid = []
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                # Garantir des nombres flottants valides
                mean_val = float(np.mean(self.current_band[y:y + 4, x:x + 4]))
                if np.isnan(mean_val) or np.isinf(mean_val):
                    mean_val = 0.0  # Corriger les valeurs invalides

                grid.append({
                    "coordinates": [int(x), int(y), int(x + 4), int(y + 4)],
                    "mean_value": round(mean_val, 6)  # Limiter la précision
                })

        # Sérialisation sécurisée
        return grid

    @staticmethod
    def serialize_grid(grid: list) -> str:
        """Sérialisation finale pour le template"""
        return json.dumps(
            grid,
            cls=DjangoJSONEncoder,
            ensure_ascii=False,
            allow_nan=False
        )

    def get_zone_data(self, x, y):
        """Calcule les moyennes des 12 bandes pour une zone 4x4"""
        grid_x = (x // 4) * 4
        grid_y = (y // 4) * 4

        band_means = {}
        for band_idx in range(self.bands.shape[0]):
            mean_value = np.mean(self.bands[
                                 band_idx,
                                 grid_y:grid_y + 4,
                                 grid_x:grid_x + 4
                                 ])
            band_means[f'Bande {band_idx + 1}'] = round(mean_value, 2)

        return band_means

