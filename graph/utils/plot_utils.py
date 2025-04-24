import pandas as pd
import plotly.express as px
from graph.models import ResultatCourse, Course, CourseType, Categorie, CategorieSimplifiee
import numpy as np
from django.db.models import Count
import plotly.graph_objects as go
# Calcul de la régression linéaire et R²
from scipy import stats
import math

def clean_nan_values(values):
    """Remplace les valeurs NaN par None dans une liste."""
    if values is None:
        return None
    return [None if (isinstance(x, float) and (np.isnan(x) or math.isnan(x))) else x for x in values]

def generate_figure(df, score_type):

    fig = go.Figure()
    # Ajouter les contours de densité pour chaque sexe
    for sexe, color, fill_color in [
        ('M', 'blue', 'rgba(0, 0, 255, 0.5)'),  # Hommes : bleu (points) et bleu clair (densité)
        ('F', 'pink', 'rgba(255, 192, 203, 0.5)')  # Femmes : rose (points) et rose clair (densité)
    ]:
        df_sexe = df[df['sexe'] == sexe]

        # Ajouter le contour de densité
        fig.add_trace(go.Histogram2dContour(
            x=df_sexe['annee'],
            y=df_sexe[f'score_de_performance_{score_type}'],
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, fill_color]],
            showscale=False,
            contours=dict(
                coloring="fill",
                showlabels=True
            ),
            line=dict(color=color, width=2),
            name=f"Densité {sexe}"
        ))

        # Calculer la droite de régression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_sexe['annee'],
            df_sexe[f'score_de_performance_{score_type}']
        )
        r_squared = r_value ** 2

        # Ajouter la droite de tendance
        x_range = np.array([df['annee'].min(), df['annee'].max()])
        y_range = slope * x_range + intercept

        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_range,
            mode='lines',
            line=dict(color=color, width=2),
            name=f"{sexe}: y = {slope:.3f}x + {intercept:.3f}, R² = {r_squared:.3f}"
        ))

    # Mettre à jour la mise en page
    fig.update_layout(
        title=f"Scores de performance ({score_type})",
        xaxis_title="Année",
        yaxis_title=f"Score de performance ({score_type})"
    )

    # Retourner le HTML pour Django
    return fig.to_html(full_html=False, include_plotlyjs=True)


def get_base_data(sample_size=10000):

    df = pd.DataFrame(
        ResultatCourse.objects.all().values(
            'id',
            'score_de_performance_vitesse',
            'score_de_performance_global',
            'categorie__sexe',
            'course__annee'
        ).order_by('?')[:sample_size]
    ).rename(columns={
        'categorie__sexe': 'sexe',
        'course__annee': 'annee'
    }).dropna()
    ids = df['id'].to_list()
    df = df[df['sexe'].isin(['M', 'F'])]
    print('len de rés : ',len(df))
    return df, ids


def generate_score_plot(df, score_type, request=None):
    """
    Génère les données formatées pour être utilisées avec Plotly.extendTraces
    """
    # Préparer les données pour les traces Plotly
    extend_data = {}  # Structure spécifique pour extendTraces
    trace_indices = {}  # Pour stocker les indices des traces à étendre
    plot_data = {}  # Format traditionnel (pour la rétrocompatibilité)

    min_year = df['annee'].min() if len(df) > 0 else None
    max_year = df['annee'].max() if len(df) > 0 else None

    # Ajouter les contours de densité pour chaque sexe
    for sexe, color, fill_color in [
        ('M', 'blue', 'rgba(0, 0, 255, 0.5)'),  # Hommes : bleu (points) et bleu clair (densité)
        ('F', 'pink', 'rgba(255, 192, 203, 0.5)')  # Femmes : rose (points) et rose clair (densité)
    ]:
        df_sexe = df[df['sexe'] == sexe]
        if len(df_sexe) > 0:
            # Format pour extendTraces - chaque type de trace a ses propres listes x et y
            extend_data[sexe] = {
                'scatter': {
                    'x': df_sexe['annee'].tolist(),
                    'y': df_sexe[f'score_de_performance_{score_type}'].tolist()
                }
            }

            # Format classique pour rétrocompatibilité
            plot_data[f'contour_{sexe}'] = {
                'x': df_sexe['annee'].tolist(),
                'y': df_sexe[f'score_de_performance_{score_type}'].tolist(),
                'colorscale':[[0, 'rgba(0,0,0,0)'], [1, fill_color]],
                'sexe': sexe
            }

            # Recalculer les tendances si nécessaire
            if len(df_sexe) >= 2:

                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    df_sexe['annee'],
                    df_sexe[f'score_de_performance_{score_type}']
                )
                r_squared = r_value ** 2

                # Préparer les données de tendance
                x_range = [float(min_year), float(max_year)]
                y_range = [
                    slope * x_range[0] + intercept,
                    slope * x_range[1] + intercept
                ]

                # Format pour extendTraces - mettre à jour la tendance
                extend_data[sexe]['trend'] = {
                    'x': x_range,
                    'y': y_range,
                    'equation': f"y = {slope:.3f}x + {intercept:.3f}, R² = {r_squared:.3f}"
                }

                # Format classique pour rétrocompatibilité
                plot_data[f'trend_{sexe}'] = {
                    'slope': slope,
                    'intercept': intercept,
                    'r_squared': r_squared
                }

    return {
        'extend_data': extend_data,  # Format optimisé pour extendTraces
        'plot_data': plot_data,  # Format original (rétrocompatibilité)
        'min_year': min_year,
        'max_year': max_year,
        'count': len(df),
        'total_displayed': request.session.get('total_displayed', 0) if request else len(df)
    }


def get_more_data(request, sample_size=10000):

    """
    Récupère un nouvel ensemble de données en excluant
    celles déjà affichées (stockées dans la session).
    """
    # Récupérer les IDs déjà affichés depuis la session
    displayed_ids = request.session.get('displayed_ids', [])
    old_results = ResultatCourse.objects.filter(
         id__in=displayed_ids
    ).values(
         'id',
         'score_de_performance_vitesse',
         'score_de_performance_global',
         'categorie__sexe',
         'course__annee'
    )

    # Requête pour obtenir de nouveaux résultats
    new_results = ResultatCourse.objects.exclude(
        id__in=displayed_ids
    ).values(
        'id',
        'score_de_performance_vitesse',
        'score_de_performance_global',
        'categorie__sexe',
        'course__annee'
    ).order_by('?')[:sample_size]
    df_old = pd.DataFrame(old_results).dropna()
    # Convertir les nouveaux résultats (que vous avez déjà fait)
    df_new = pd.DataFrame(new_results).dropna()
    df_full = pd.concat([df_old, df_new])
    df = df_new
    df.rename(columns={'categorie__sexe': 'sexe','course__annee': 'annee'}, inplace=True)
    df_full.rename(columns={'categorie__sexe': 'sexe','course__annee': 'annee'}, inplace=True)
    # Filtrer seulement H et F
    df = df[df['sexe'].isin(['M', 'F'])]
    df_full = df_full[df_full['sexe'].isin(['M', 'F'])]
    print('len de new df',len(df_full))
    # Mettre à jour la session avec les nouveaux IDs
    new_ids = df['id'].astype(str).tolist()
    request.session['displayed_ids'] = displayed_ids + new_ids
    request.session['total_displayed'] = len(displayed_ids) + len(new_ids)

    print(f'Nouvelles données : {len(df)} lignes, Total affiché : {request.session["total_displayed"]}')
    return df_full


def evolution_types_courses():
    # Récupération des données groupées par année et type
    queryset = Course.objects.values('annee', 'type_id__nom').annotate(
        total=Count('id')
    ).order_by('annee')

    # Structuration des données pour le template
    evolution_data = {}
    for entry in queryset:
        annee = entry['annee']
        type_name = entry['type_id__nom']
        count = entry['total']

        if annee not in evolution_data:
            evolution_data[annee] = {}
        evolution_data[annee][type_name] = count

    # Création du graphique avec Plotly
    fig  = px.line(
        title="Évolution des types de courses par année",
        labels={'value': 'Nombre de courses', 'variable': 'Type de course'},
        width=600  # Limite la largeur à 300 pixels
    )

    fig.update_layout(
        xaxis=dict(title='Année'),
        yaxis=dict(title="Nombre de courses enregistrées pour l'année"),
    )

    # Préparation des données pour Plotly
    types = CourseType.objects.values_list('nom', flat=True).distinct()
    years = sorted(evolution_data.keys())

    for type_name in types:
        counts = [evolution_data.get(year, {}).get(type_name, 0) for year in years]
        fig.add_scatter(x=years, y=counts, name=type_name, mode='lines+markers')

    # Conversion du graphique en HTML
    plot_html = fig.to_html(full_html=False)

    return plot_html


def evolution_vitesse_par_categorie(categorie_simplifiee_id):
    """
    Génère un graphique d'évolution de la vitesse moyenne pour 10km et semi-marathon
    pour une catégorie simplifiée donnée, avec affichage des écarts-types.
    """
    # Structure correcte des distances
    distance_map = {
        '10km': [10000],
        'Semi-marathon': [21097, 21100]
    }

    # Applatir la liste pour la requête Django
    distances_list = []
    for dist_values in distance_map.values():
        distances_list.extend(dist_values)

    # Années à considérer
    annees = list(range(2014, 2025))

    # Récupérer les catégories liées à la catégorie simplifiée
    categories_ids = Categorie.objects.filter(
        categoriesimplifiee_id=categorie_simplifiee_id
    ).values_list('id', flat=True)

    # Récupérer les résultats de course pertinents
    resultats_qs = ResultatCourse.objects.filter(
        course__type_id__nom__in=['Course sur route', 'Foulée'],
        course__distance__in=distances_list,
        course__annee__in=annees,
        categorie_id__in=categories_ids
    ).select_related('course')

    # Convertir en DataFrame
    data = []
    for resultat in resultats_qs:
        temps_total = resultat.temps or resultat.temps2
        if temps_total:
            secondes = temps_total.total_seconds()
            distance = resultat.course.distance
            annee = resultat.course.annee

            # Calculer la vitesse en km/h
            if secondes > 0:
                vitesse = (distance / 1000) / (secondes / 3600)
                # Filtrer les vitesses aberrantes
                if 6 <= vitesse <= 25:
                    data.append({
                        'annee': annee,
                        'distance': distance,
                        'vitesse': vitesse
                    })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Si le DataFrame est vide, renvoyer un graphique vide
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title='Aucune donnée disponible pour cette catégorie',
            xaxis=dict(title='Année'),
            yaxis=dict(title='Vitesse moyenne (km/h)')
        )
        return fig.to_html(full_html=False)

    # Définir les couleurs pour les différentes distances
    colors = {
        '10km': 'rgb(31, 119, 180)',
        'Semi-marathon': 'rgb(255, 127, 14)'
    }

    # Créer le graphique
    fig = go.Figure()

    # Pour chaque type de distance, calculer la moyenne et les écarts-types par année
    for distance_name, distance_values in distance_map.items():
        # Filtrer le DataFrame pour les distances correspondantes
        df_dist = df[df['distance'].isin(distance_values)]

        if not df_dist.empty:
            color = colors[distance_name]
            # Calculer les statistiques par année
            stats = []
            for annee in annees:
                df_annee = df_dist[df_dist['annee'] == annee]
                if not df_annee.empty:
                    moyenne = df_annee['vitesse'].mean()

                    # Calcul de l'écart supérieur (moyenne des écarts positifs)
                    df_haut = df_annee[df_annee['vitesse'] > moyenne]
                    ecart_haut = (df_haut['vitesse'] - moyenne).mean() if not df_haut.empty else 0

                    # Calcul de l'écart inférieur (moyenne des écarts négatifs)
                    df_bas = df_annee[df_annee['vitesse'] < moyenne]
                    ecart_bas = (moyenne - df_bas['vitesse']).mean() if not df_bas.empty else 0

                    stats.append({
                        'annee': annee,
                        'moyenne': moyenne,
                        'ecart_haut': moyenne + ecart_haut,
                        'ecart_bas': moyenne - ecart_bas
                    })
                else:
                    stats.append({
                        'annee': annee,
                        'moyenne': None,
                        'ecart_haut': None,
                        'ecart_bas': None
                    })

            # Convertir en DataFrame pour faciliter le tracé
            df_stats = pd.DataFrame(stats)

            # Tracer la ligne de moyenne
            fig.add_trace(go.Scatter(
                x=df_stats['annee'],
                y=df_stats['moyenne'],
                mode='lines+markers',
                name=distance_name,
                line=dict(color=color, width=2)
            ))

            # Ajouter la zone d'écart-type (zone colorée entre les écarts)
            fig.add_trace(go.Scatter(
                x=df_stats['annee'].tolist() + df_stats['annee'].tolist()[::-1],
                y=df_stats['ecart_haut'].tolist() + df_stats['ecart_bas'].tolist()[::-1],
                fill='toself',
                fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name=f'{distance_name} (écart-type)'
            ))

    # Configurer le layout du graphique
    categorie_nom = CategorieSimplifiee.objects.get(id=categorie_simplifiee_id).nom

    fig.update_layout(
        title=f'Évolution de la vitesse moyenne par distance pour {categorie_nom}.',
        xaxis=dict(title='Année', tickmode='linear'),
        yaxis=dict(title='Vitesse moyenne (km/h)', range=[6, 20]),
        legend=dict(title='Distance'),
        hovermode='x unified',
        width=600
    )

    # Renvoyer le HTML du graphique
    return fig.to_html(full_html=False)


def evolution_vitesse_par_categorie_data(categorie_simplifiee_id):
    """
    Génère les données d'évolution des vitesses moyennes au format JSON
    compatible avec Plotly.react pour du rendu côté client.
    """
    # Structure des distances
    distance_map = {
        '10km': [10000],
        'Semi-marathon': [21097, 21100]
    }

    # Aplatir la liste pour la requête Django
    distances_list = []
    for dist_values in distance_map.values():
        distances_list.extend(dist_values)

    # Années à considérer
    annees = list(range(2014, 2025))

    # Récupérer les catégories liées
    categories_ids = Categorie.objects.filter(
        categoriesimplifiee_id=categorie_simplifiee_id
    ).values_list('id', flat=True)

    # Récupérer les résultats de course pertinents
    resultats_qs = ResultatCourse.objects.filter(
        course__type_id__nom__in=['Course sur route', 'Foulée'],
        course__distance__in=distances_list,
        course__annee__in=annees,
        categorie_id__in=categories_ids
    ).select_related('course')

    # Convertir en DataFrame
    data = []
    for resultat in resultats_qs:
        temps_total = resultat.temps or resultat.temps2
        if temps_total:
            secondes = temps_total.total_seconds()
            distance = resultat.course.distance
            annee = resultat.course.annee

            # Calculer la vitesse en km/h
            if secondes > 0:
                vitesse = (distance / 1000) / (secondes / 3600)
                if 6 <= vitesse <= 25:
                    data.append({
                        'annee': annee,
                        'distance': distance,
                        'vitesse': vitesse
                    })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # Préparer la structure des données Plotly
    traces = []

    # Informations pour le layout
    categorie_nom = CategorieSimplifiee.objects.get(id=categorie_simplifiee_id).nom
    layout = {
        'title': f'Évolution de la vitesse moyenne par distance pour {categorie_nom}.',
        'xaxis': {'title': 'Année', 'tickmode': 'linear'},
        'yaxis': {'title': 'Vitesse moyenne (km/h)', 'range': [6, 20]},
        'legend': {'title': 'Distance'},
        'hovermode': 'x unified'
    }

    # Si le DataFrame est vide, renvoyer un objet vide
    if df.empty:
        return {'data': [], 'layout': layout}

    # Définir les couleurs pour les différentes distances
    colors = {
        '10km': 'rgb(31, 119, 180)',
        'Semi-marathon': 'rgb(255, 127, 14)'
    }

    # Pour chaque type de distance, calculer les statistiques
    for distance_name, distance_values in distance_map.items():
        # Filtrer le DataFrame pour les distances correspondantes
        df_dist = df[df['distance'].isin(distance_values)]

        if not df_dist.empty:
            color = colors[distance_name]

            # Calculer les statistiques par année
            stats = []
            for annee in annees:
                df_annee = df_dist[df_dist['annee'] == annee]
                if not df_annee.empty:
                    moyenne = df_annee['vitesse'].mean()

                    # Calcul des écarts
                    df_haut = df_annee[df_annee['vitesse'] > moyenne]
                    ecart_haut = (df_haut['vitesse'] - moyenne).mean() if not df_haut.empty else 0

                    df_bas = df_annee[df_annee['vitesse'] < moyenne]
                    ecart_bas = (moyenne - df_bas['vitesse']).mean() if not df_bas.empty else 0

                    stats.append({
                        'annee': annee,
                        'moyenne': moyenne,
                        'ecart_haut': moyenne + ecart_haut,
                        'ecart_bas': moyenne - ecart_bas
                    })
                else:
                    stats.append({
                        'annee': annee,
                        'moyenne': None,
                        'ecart_haut': None,
                        'ecart_bas': None
                    })

            # Convertir en DataFrame
            df_stats = pd.DataFrame(stats)

            # Ligne de moyenne
            traces.append({
                'type': 'scatter',
                'x': clean_nan_values(df_stats['annee'].tolist()),
                'y': clean_nan_values(df_stats['moyenne'].tolist()),
                'mode': 'lines+markers',
                'name': distance_name,
                'line': {'color': color, 'width': 2}
            })

            # Zone d'écart-type
            traces.append({
                'type': 'scatter',
                'x': clean_nan_values(df_stats['annee'].tolist() + df_stats['annee'].tolist()[::-1]),
                'y': clean_nan_values(df_stats['ecart_haut'].tolist() + df_stats['ecart_bas'].tolist()[::-1]),
                'fill': 'toself',
                'fillcolor': color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                'line': {'color': 'rgba(255,255,255,0)'},
                'showlegend': False,
                'name': f'{distance_name} (écart-type)'
            })

    # Retourner les données au format compatible avec Plotly.react
    return {
        'data': traces,
        'layout': layout
    }

