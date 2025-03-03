from dash import dcc, html
from django_plotly_dash import DjangoDash

app = DjangoDash('SimpleApp', serve_locally=False)

app.layout = html.Div([
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'}],
            'layout': {'title': 'Dash Example'}
        }
    )
])