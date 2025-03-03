import os
import glob
from datetime import datetime, timedelta

import rasterio as rio
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from DataTest import settings


def extract_date_from_filename(filepath):
    # Extraire le nom du fichier du chemin complet
    filename = os.path.basename(filepath)
    # Extraire la date du nom du fichier
    date_str = filename.split('_')[0]
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def create_ndvi_cube():
    path = r'C:\Users\33682\PycharmProjects\DataTest\agri\static\satellite_data\Boulinsard\12bands'
    imgs_list = glob.glob(os.path.join(path, "*.TIFF"))
    # Trier les images par date
    filenames = [os.path.basename(img) for img in imgs_list]
    # Extraire les dates et trier les images par date
    dates_and_files = [(extract_date_from_filename(img), img) for img in imgs_list]
    dates_and_files.sort(key=lambda x: x[0])

    sorted_dates = [item[0] for item in dates_and_files]
    sorted_files = [item[1] for item in dates_and_files]

    first_date = sorted_dates[0]
    last_date = sorted_dates[-1]

    # Calculer les NDVI pour les dates disponibles
    ndvi_by_date = {}
    for date, file in zip(sorted_dates, sorted_files):
        matrix = rio.open(file)
        B4 = matrix.read(4).astype(float)
        B8 = matrix.read(8).astype(float)

        denominator = B8 + B4
        NDVI = np.zeros_like(B4)
        valid_pixels = denominator != 0
        NDVI[valid_pixels] = (B8[valid_pixels] - B4[valid_pixels]) / denominator[valid_pixels]

        ndvi_by_date[date] = NDVI

    # Créer un NDVI pour chaque jour
    all_dates = []
    all_ndvis = []
    current_date = first_date
    last_ndvi = None

    while current_date <= last_date:
        if current_date in ndvi_by_date:
            last_ndvi = ndvi_by_date[current_date]

        if last_ndvi is not None:
            all_dates.append(current_date)
            all_ndvis.append(last_ndvi)

        current_date += timedelta(days=7)

    # Calculer les jours écoulés depuis la première date
    days_elapsed = [(date - first_date).days for date in all_dates]

    # Créer le cube NDVI
    ndvi_cube = np.stack(all_ndvis, axis=-1)

    return ndvi_cube, all_dates, days_elapsed


def generate_ndvi_plot(ndvi_cube):
    x, y, z = np.indices(ndvi_cube.shape)

    fig = go.Figure(data=go.Volume(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        value=ndvi_cube.flatten(),
        isomin=0.69,
        isomax=0.83,
        opacity=0.07,
        surface_count=20,
        colorscale='Viridis',
        colorbar=dict(
            title="Intensité du NDVI",
            titleside="right",
            titlefont=dict(
                size=14,
                family="Arial"
            )
        )
    ))

    fig.update_layout(scene=dict(
        xaxis_title='Décamètres Nord-Sud',
        yaxis_title='Décamètres Est-Ouest',
        zaxis_title='Semaines'
    )
)




    return pio.to_html(fig, full_html=False)