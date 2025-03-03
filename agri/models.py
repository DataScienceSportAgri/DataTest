# models.py
from django.db import models
import os
from django.conf import settings


class SatelliteImage:
    def __init__(self, date):
        self.date = date
        # Chemin vers l'image TIFF multi-bandes
        self.tiff_path = os.path.join('satellite_data', 'Boulinsard', '12bands', f'{date}_S2A-12band.TIFF')
        # Chemin vers l'image lai
        self.lai_path = os.path.join('satellite_data', 'Boulinsard', 'lai', f'{date}_LAI.jpg')

    def get_band(self, band_index):
        """Récupère une bande spécifique de l'image TIFF"""
        import rasterio
        with rasterio.open(self.tiff_path) as src:
            return src.read(band_index)


class Parcel(models.Model):
    name = models.CharField(max_length=100)

    def get_available_dates(self):
        """Récupère les dates disponibles en parcourant le dossier"""
        tiff_dir = os.path.join(settings.STATIC_ROOT, 'satellite_data','Boulinsard', '12bands')
        dates = []
        for file in os.listdir(tiff_dir):
            if file.endswith('12band.TIFF'):
                date = file.split('_')[0]
                dates.append(date)
        return sorted(dates)

    def get_image_for_date(self, date):
        """Retourne un objet SatelliteImage pour une date donnée"""
        return SatelliteImage(date)