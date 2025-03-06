import os
import glob
from datetime import datetime, timedelta

import pandas as pd
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
    path = os.path.join(settings.BASE_DIR, 'agri', 'static', 'satellite_data', 'Boulinsard', '12bands')
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

    current_date = first_date

    all_ndvis = []
    rows = []
    last_ndvi = ndvi_by_date[first_date]
    sorted_date_number = 0
    number = 0
    print('sorted_date',sorted_dates)
    while sorted_date_number < len(sorted_dates)-1:
        if sorted_dates[sorted_date_number+1] > current_date:
            number += 1
            sorted_date = sorted_dates[sorted_date_number]
            rows.append({
                'sorted_date': sorted_date,
                'layer_date': current_date,
                'number': number
            })
            print('rows',rows)
            last_ndvi = ndvi_by_date[sorted_date]
            all_ndvis.append(last_ndvi)
        else:
            sorted_date_number += 1
            sorted_date = sorted_dates[sorted_date_number]
            number = 1
            rows.append({
                'sorted_date': sorted_date,
                'layer_date': current_date,
                'number': number
            })
            last_ndvi = ndvi_by_date[sorted_date]
            all_ndvis.append(last_ndvi)
        current_date += timedelta(days=4)
    number = 0
    while current_date <= last_date:
        number +=1
        sorted_date = sorted_dates[-1]
        rows.append({
            'sorted_date': sorted_date,
            'layer_date': current_date,
            'number': number
        })
        last_ndvi = ndvi_by_date[sorted_date]
        all_ndvis.append(last_ndvi)
        current_date += timedelta(days=4)


        # Passer à la semaine suivante

    # Créer le DataFrame final
    sorted_date_to_current_date = pd.DataFrame(rows)
    print(sorted_date_to_current_date)
    # Créer le cube NDVI
    print('cube',len(all_ndvis))
    ndvi_cube = np.stack(all_ndvis, axis=-1)
    return ndvi_cube, sorted_date_to_current_date


def generate_ndvi_plot(ndvi_cube, layer, thickness):
    x, y, z = np.indices(ndvi_cube.shape)
    print('x',x)
    print('y',y)
    print('z',z)
    # Création du tracé volumétrique principal
    fig = go.Figure(data=go.Volume(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        value=ndvi_cube.flatten(),
        isomin=0.16,
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

    # Ajout d'un volume d'épaisseur 1 autour de la couche spécifique
    z_layer = layer  # Indice de la couche à mettre en surbrillance
    thickness = thickness +1  # Épaisseur du volume

    # Générer les coordonnées pour le volume d'épaisseur 1
    z_volume = np.arange(z_layer, z_layer + thickness)  # Plage de z pour l'épaisseur
    x_volume, y_volume, z_volume_mesh = np.meshgrid(
        np.arange(ndvi_cube.shape[0]),
        np.arange(ndvi_cube.shape[1]),
        z_volume,
        indexing='ij'
    )

    # Répéter les données NDVI pour chaque tranche dans l'épaisseur
    layer_data_volume = np.repeat(ndvi_cube[:, :, z_layer][:, :, np.newaxis], thickness, axis=2)

    fig.add_trace(go.Volume(
        x=x_volume.flatten(),
        y=y_volume.flatten(),
        z=z_volume_mesh.flatten(),
        value=layer_data_volume.flatten(),  # Utiliser les valeurs NDVI répétées
        colorscale='Magma',  # Appliquer l'échelle de couleurs Magma
        cmin=0.69,
        cmax=0.83,
        opacity=0.2,  # Opacité légèrement plus élevée pour mise en surbrillance
        showscale=False  # Désactiver la barre d'échelle pour ce volume spécifique
    ))

    # Mise à jour des axes et des titres
    fig.update_layout(scene=dict(
        xaxis_title='Décamètres Nord-Sud',
        yaxis_title='Décamètres Est-Ouest',
        zaxis_title='Semaines',
        aspectmode="cube"  # Maintenir une proportion uniforme des axes
    ),
        paper_bgcolor='rgba(0,0,0,0)',  # Fond transparent du graphique
        plot_bgcolor='rgba(0,0,0,0)'  # Fond transparent du tracé
    )

    return pio.to_html(fig, full_html=False)