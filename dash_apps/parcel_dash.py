# Déclaration globale obligatoire
from venv import logger
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np
from dash.exceptions import PreventUpdate
from django.db.models.functions import datetime
from django_plotly_dash import DjangoDash
from django.conf import settings
import rasterio

parcel_dash = DjangoDash(
    'Parcel3DViewer',
    serve_locally=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        '/static/dash/component/dash_bootstrap_components/_components/dash_bootstrap_components.min.css'
    ]
)
parcel_dash.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H1("Dashboard Avancé", className="text-center mb-4"),
            width=12
        )
    ),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='3d-ndvi-cube'),
            md=9
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody("Paramètres"),
                color="light"
            ),
            md=3
        )
    ])
], fluid=True)
@parcel_dash.callback(
    Output('debug-output', 'children'),
    [Input('cube-store', 'data'), Input('dates-store', 'data')]
)
def debug_stores(cube_data, dates_data):
    if not cube_data:
        return "Cube NDVI non chargé."
    if not dates_data:
        return "Dates non chargées."
    return f"Cube NDVI chargé avec {len(cube_data)} couches temporelles et {len(dates_data)} dates."
def load_tiff_files(parcel_name, os=None):
    """Remplace la méthode _load_tiff_files de la classe"""
    base_path = os.path.join(settings.STATIC_ROOT, 'satellite_data', parcel_name, '12bands')

    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"Dossier introuvable: {base_path}")

    files = []
    for fname in sorted(os.listdir(base_path)):
        if fname.upper().endswith('.TIFF'):
            full_path = os.path.join(base_path, fname)
            if os.path.isfile(full_path):
                date_str = fname.split('_')[0]
                files.append((
                    datetime.strptime(date_str, '%Y-%m-%d'),
                    full_path
                ))

    if not files:
        raise ValueError("Aucun fichier TIFF valide trouvé")

    return sorted(files, key=lambda x: x[0])


def create_ndvi_cube(tiff_files):
    """Remplace _create_data_cube"""
    cube = []
    for _, path in tiff_files:
        with rasterio.open(path) as src:
            nir = src.read(8).astype('f4')
            red = src.read(4).astype('f4')
            cube.append((nir - red) / (nir + red + 1e-9))
    return np.dstack(cube)





@parcel_dash.callback(
    [Output('cube-store', 'data'),
     Output('dates-store', 'data'),
     Output('time-slider', 'max'),
     Output('time-slider', 'marks')],
    [Input('_dash-app-relayout', 'modified_timestamp')],
    [State('_dash-app-relayout', 'data')]
)
def initialize_data(ts, _):
    """Remplace l'initialisation de Parcel3DVisualizer"""
    if ts is None:
        raise PreventUpdate

    try:
        tiff_files = load_tiff_files("Boulinsard")
        cube = create_ndvi_cube(tiff_files)
        dates = [dt.strftime("%Y-%m-%d") for dt, _ in tiff_files]

        marks = {i: {'label': date, 'style': {'color': '#fff'}}
                 for i, date in enumerate(dates)}

        return (
            cube.tolist(),
            dates,
            len(dates) - 1,
            marks
        )
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return [None] * 4



@parcel_dash.callback(
    Output('3d-ndvi-cube', 'figure'),
    [Input('cube-store', 'data'),
     Input('time-slider', 'value')]
)
def update_visualization(cube_data, selected_layer):
    if not cube_data:
        return go.Figure()

    cube = np.array(cube_data)
    x, y, z = np.indices(cube.shape)

    # Crée le volume principal
    fig = go.Figure(go.Volume(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        value=cube.flatten(),
        isomin=0.1,
        isomax=0.9,
        opacity=0.05,
        surface_count=25,
        colorscale='magma'
    ))

    # Ajoute la couche en surbrillance
    if selected_layer is not None:
        fig.add_trace(go.Surface(
            z=selected_layer * np.ones_like(cube[:, :, selected_layer]),
            surfacecolor=cube[:, :, selected_layer],
            colorscale='magma',
            opacity=0.7,
            showscale=False
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Temps',
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8))
        ),
        margin=dict(l=0, r=0, b=20, t=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig
