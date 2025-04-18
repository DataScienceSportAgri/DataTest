# utils.py
import numpy as np
import pandas as pd
from django.db.models import Q
from graph.models import Coureur, ResultatCourse
import json
from scipy import stats
import re
import statsmodels.api as sm
import statsmodels.formula.api as smf


def get_coureurs_by_count(df, group_col='groupe', n=30):
    """
    Sélectionne les n coureurs avec le plus grand nombre de résultats dans chaque groupe.

    Parameters:
    -----------
    df : DataFrame
        DataFrame contenant les données des coureurs
    group_col : str, default='groupe'
        Colonne utilisée pour le regroupement
    n : int, default=30
        Nombre de coureurs à conserver par groupe

    Returns:
    --------
    DataFrame
        DataFrame filtré avec les top n coureurs par groupe
    """
    # Compter le nombre de résultats par coureur dans chaque groupe
    counts_by_coureur = df.groupby(['coureur_id', group_col]).size().reset_index(name='count')

    # Sélectionner les top n coureurs par nombre de résultats dans chaque groupe
    top_coureurs = (counts_by_coureur.sort_values(by='count', ascending=False)
                    .groupby(group_col)
                    .head(n))

    # Créer un masque pour filtrer le DataFrame original
    coureurs_mask = df['coureur_id'].isin(top_coureurs['coureur_id'])

    return df[coureurs_mask]


def filter_and_aggregate_time_series(df):
    # Filtrer les coureurs qui n'ont qu'une seule année de données
    counts = df.groupby('coureur_id')['annee'].nunique()
    coureurs_to_keep = counts[counts > 1].index
    df_filtered = df[df['coureur_id'].isin(coureurs_to_keep)]

    if len(df_filtered) == 0:
        print("Aucun coureur avec plusieurs années de données!")
        return df  # Retourner les données originales si aucun coureur valide

    # Agréger les scores par coureur et par année (moyenne)
    df_agg = df_filtered.groupby(['coureur_id', 'annee'], as_index=False).agg({
        'score': 'median',
        'nom_marsien': 'first',
        'prenom_marsien': 'first',
        'groupe': 'first'  # Ajouter cette ligne pour conserver le groupe
    })

    return df_agg


# Nouvelle fonction utilitaire pour générer les labels safe
def generate_safe_label(raw_label):
    # Remplacer tous les caractères non alphanumériques par des underscores
    return re.sub(r'[^a-zA-Z0-9]', '_', str(raw_label)).lower()

# Conversion des types NumPy en types Python
def convert_numpy_types(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def get_color_for_group(groupe):
    """
    Retourne une couleur hexadécimale ou RGB pour un groupe donné.
    """
    groupe_safe = re.sub(r'[^a-zA-Z0-9]', '_', str(groupe)).lower()
    # Palette personnalisée (exemple pour 6 groupes)
    palette = [
        "#1f77b4", # bleu
        "#ff7f0e", # orange
        "#2ca02c", # vert
        "#d62728", # rouge
        "#9467bd", # violet
        "#8c564b", # marron
        "#e377c2", # rose
        "#7f7f7f", # gris
        "#bcbd22", # olive
        "#17becf"  # cyan
    ]
    # Associer chaque label à une couleur (ordre stable)
    labels = [
        '0-25%', '25-50%', '50-75%', '75-100%',
        'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'Top 20%',
        'V1', 'V2', 'V3', 'V4', 'V5', 'V6'
    ]

    return palette[hash(groupe_safe) % len(palette)]

def get_filtered_coureurs(coureur_type='viables'):
    """Filtre les coureurs selon le type demandé"""
    if coureur_type == 'viables':
        return Coureur.objects.filter(score_de_viabilite__gt=0.3)
    elif coureur_type == 'tous':
        random_coureurs = Coureur.objects.order_by('?')[:10000]
        return random_coureurs
    raise ValueError("Type de coureur invalide")


def calculate_percentile_groups(scores, distribution_type='quartiles'):
    """
    Retourne :
    - Une Series pandas avec des labels CSS-safe
    - Un dictionnaire de mapping {label_safe: label_affichage}
    """
    if distribution_type == 'quartiles':
        bins = np.quantile(scores, [0, 0.25, 0.5, 0.75, 1.0])
        labels_affichage = ['0-25%', '25-50%', '50-75%', '75-100%']
        labels_safe = ['q1', 'q2', 'q3', 'q4']  # Noms sans caractères spéciaux
    elif distribution_type == 'deciles':
        bins = np.quantile(scores, np.linspace(0, 1, 11))
        labels_affichage = [f'{i * 10}-{(i + 1) * 10}%' for i in range(10)]
        labels_safe = [f'd{i + 1}' for i in range(10)]
    elif distribution_type == 'ventiles':
        bins = np.quantile(scores, np.linspace(0, 1, 21))
        labels_affichage = [f'{i * 5}-{(i + 1) * 5}%' for i in range(20)]
        labels_safe = [f'v{i + 1}' for i in range(20)]
    else:
        raise ValueError("Type de distribution invalide")

    groupes = pd.cut(scores, bins=bins, labels=labels_safe, include_lowest=True)
    label_map = dict(zip(labels_safe, labels_affichage))
    groupes.label_map = label_map  # Stockage du mapping

    return groupes



def hub_processing(coureur_type='viables', distribution_type='quartiles', score_type='global'):
    """
    Traitement principal déterminé par coureur_type :
    - 'viables' : Séries temporelles par coureur (moyennes)
    - 'tous' : Tous les points individuels
    """
    # 1. Récupération des données de base
    coureurs = get_filtered_coureurs(coureur_type)

    # 2. Chargement des résultats
    resultats = ResultatCourse.objects.filter(
        Q(coureur__in=coureurs) &
        Q(course__type_id__in=[1, 7, 8, 9])
    ).select_related('course').values(
        'coureur__nom_marsien',
        'coureur__prenom_marsien',
        'coureur_id',
        'course__annee',
        f'score_de_performance_{score_type}'
    )

    df = pd.DataFrame(resultats).rename(columns={
        'coureur__nom_marsien' : 'nom_marsien',
        'coureur__prenom_marsien' : 'prenom_marsien',
        'course__annee': 'annee',
        f'score_de_performance_{score_type}' : 'score'
    })

    # 3. Calcul des groupes selon le type de coureur
    if coureur_type == 'viables':
        # Agrégation par coureur
        df_agg = df.groupby('coureur_id', as_index=False)['score'].mean()
        df_agg['groupe'] = calculate_percentile_groups(df_agg['score'], distribution_type)
        df = df.merge(df_agg[['coureur_id', 'groupe']], on='coureur_id')
    else:
        # Tous les points individuels
        df['groupe'] = calculate_percentile_groups(df['score'], distribution_type)

    # 4. Structuration des données de sortie
    series_par_groupe = {}

    # Ajouter les noms dans les données de sortie
    noms_coureurs = dict(Coureur.objects.values_list('id', 'nom'))

    for groupe, group_df in df.groupby('groupe'):
        if coureur_type == 'viables':
            series_par_groupe[groupe] = [
                {
                    'coureur_id': cid,
                    'nom': noms_coureurs.get(cid, 'Inconnu'),
                    'dates': cdf['annee'].tolist(),
                    'scores': cdf['score'].tolist(),
                    'color': get_color_for_group(groupe)  # Fonction à implémenter
                }
                for cid, cdf in group_df.groupby('coureur_id')
            ]
        else:
            series_par_groupe[groupe] = [{
                'date': row['annee'],
                'score': row['score'],
                'coureur_id': row['coureur_id'],
                'nom': noms_coureurs.get(row['coureur_id'], 'Inconnu')
            } for _, row in group_df.iterrows()]

    series_formatees = []

    # Créer un dictionnaire pour stocker les tendances par groupe
    tendances_par_groupe = {}

    if coureur_type == 'viables':
        # 1. Pour chaque groupe
        for groupe, group_df in df.groupby('groupe'):
            # 2. Filtrer et agréger les données du groupe
            group_df_processed = filter_and_aggregate_time_series(group_df)
            print('group_df_processed', group_df_processed)
            # 2. Sélectionner les 30 coureurs avec le plus de points dans ce groupe
            top_coureurs_df = get_coureurs_by_count(group_df_processed, group_col='groupe', n=30)
            groupe_safe = generate_safe_label(group_df_processed)

            # 3. Ajouter toutes les séries individuelles sélectionnées
            for coureur_id, coureur_df in top_coureurs_df.groupby('coureur_id'):
                values = [
                    {"date": int(annee), "score": float(score), "coureur_id": coureur_id,
                     "prenom_marsien": prenom, "nom_marsien": nom}
                    for annee, score, coureur_id, prenom, nom in zip(
                        coureur_df['annee'], coureur_df['score'],
                        coureur_df['coureur_id'], coureur_df['nom_marsien'], coureur_df['prenom_marsien'])
                ]
                series_formatees.append({
                    "nom": noms_coureurs.get(coureur_id, f"Coureur {coureur_id}"),
                    "coureur_id": coureur_id,
                    "values": values,
                    "color": get_color_for_group(groupe),
                    "type": "individual",
                    'groupe_safe': groupe_safe
                })

            # 4. Calculer la tendance sur ces coureurs sélectionnés
            if len(top_coureurs_df) > 2:
                data = calculate_group_trends(top_coureurs_df, max_iter=100)
                series_formatees.append({
                    "nom": f"Tendance groupe {groupe}",
                    "groupe": groupe,
                    "trend": True,
                    "min_year": int(top_coureurs_df['annee'].min()),
                    "max_year": int(top_coureurs_df['annee'].max()),
                    "slope": float(data['avg_slope']),
                    "intercept": float(data['avg_intercept']),
                    "group_variance": data['group_variance'],
                    "color": get_color_for_group(groupe),
                    "type": "trend",
                    'groupe_safe': groupe_safe
                })


    else:
        # Pour 'tous' : ne pas créer de séries par coureur, mais par groupe uniquement
        # et indiquer qu'il s'agit de scatter points + trendline
        for groupe, group_df in df.groupby('groupe'):
            groupe_safe = generate_safe_label(groupe)
            points = [
                {"date": int(row['annee']), "score": float(row['score']), "coureur_id": row['coureur_id'], "nom_marsien":row['nom_marsien'], "prenom_marsien":row['prenom_marsien']}
                for _, row in group_df.iterrows()
            ]
            series_formatees.append({
                "nom": f"Groupe {groupe}",
                "groupe": groupe,
                "points": points,  # Tous les points de ce groupe
                "color": get_color_for_group(groupe),
                "type": "group",
                'groupe_safe': groupe_safe  # <-- Ajout ici

            })

            # Calculer aussi les données pour la ligne de tendance
            x_values = group_df['annee'].astype(float).values
            y_values = group_df['score'].values

            if len(x_values) > 1:  # S'assurer qu'il y a assez de points
                # Régression linéaire simple
                slope, intercept = np.polyfit(x_values, y_values, 1)

                # Calculer les points de la ligne de tendance
                min_year = int(min(x_values))
                max_year = int(max(x_values))

                # Ajouter la ligne de tendance aux données
                series_formatees.append({
                    "nom": f"Tendance groupe {groupe}",
                    "groupe": groupe,
                    "trend": True,
                    "min_year": min_year,
                    "max_year": max_year,
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "color": get_color_for_group(groupe),
                    "type": "trend",
                    'groupe_safe': groupe_safe  # <-- Ajout ici
                })
            if len(x_values) > 2:  # Besoin d'au moins 3 points pour l'intervalle de confiance
                # Régression linéaire avec stats pour obtenir plus d'informations
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)

                # Calculer les valeurs prédites
                y_pred = slope * x_values + intercept

                # Calculer les résidus
                residuals = y_values - y_pred

                # Écart-type des résidus (pour l'intervalle de confiance)
                residual_std = np.std(residuals)

                # Ajouter la ligne de tendance avec intervalle de confiance
                series_formatees.append({
                    "nom": f"Tendance groupe {groupe}",
                    "groupe": groupe,
                    "trend": True,
                    "min_year": int(min(x_values)),
                    "max_year": int(max(x_values)),
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "std_err": float(std_err),
                    "residual_std": float(residual_std),
                    "color": get_color_for_group(groupe),
                    "type": "trend",
                    'groupe_safe': groupe_safe  # <-- Ajout ici
                })
            # Nouvelle fonction utilitaire pour générer les labels safe



        # Appliquez la conversion à toutes les données
    series_formatees = json.loads(json.dumps(series_formatees, default=convert_numpy_types))
    # 5. Calcul des tendances globales
    tendances = {}
    for groupe, data in series_par_groupe.items():
        if coureur_type == 'viables':
            # Tendances des séries temporelles
            df_trend = pd.DataFrame([
                (d, s) for serie in data for d, s in zip(serie['dates'], serie['scores'])
            ], columns=['date', 'score'])
        else:
            # Tendances des points bruts
            df_trend = pd.DataFrame(data)[['date', 'score']]

        df_trend['date'] = pd.to_datetime(df_trend['date'], format='%Y')
        tendances[groupe] = df_trend.groupby(pd.Grouper(key='date', freq='Y')).agg({
            'score': ['median', 'mean', 'std']
        })
    return {
        'series': series_par_groupe,
        'series_formatees': series_formatees,  # Inclus dans le dictionnaire
        'tendances': tendances,
        'metadata': {
            'coureur_type': coureur_type,
            'distribution_type': distribution_type,
            'score_type': score_type
        }
    }


def calculate_global_trends(series_par_groupe, coureur_type='viables'):
    """Calcule les tendances globales en fonction du type de données"""
    tendances = {}

    for groupe, series in series_par_groupe.items():
        # Détection automatique du type de données
        if isinstance(series, list) and all('dates' in s for s in series):
            # Cas des séries temporelles (coureur_type='viables')
            df = pd.DataFrame([
                (date, score)
                for serie in series
                for date, score in zip(serie['dates'], serie['scores'])
            ], columns=['date', 'score'])
        else:
            # Cas des points individuels (coureur_type='tous')
            df = pd.DataFrame([
                (point['date'], point['score'])
                for point in series
            ], columns=['date', 'score'])

        # Conversion et traitement temporel
        df['date'] = pd.to_datetime(df['date'], format='%Y')
        df.set_index('date', inplace=True)

        # Agrégation différenciée
        if coureur_type == 'viables':
            # Rééchantillonnage annuel avec interpolation linéaire
            df_resampled = df.resample('Y').mean().interpolate()
        else:
            # Agrégation annuelle simple
            df_resampled = df.resample('Y').agg(['median', 'mean', 'std'])

        # Formatage des résultats
        tendances[groupe] = {
            'dates': df_resampled.index.strftime('%Y').tolist(),
            'median': df_resampled['score']['median'].tolist() if coureur_type == 'tous' else df_resampled['score'].tolist(),
            'mean': df_resampled['score']['mean'].tolist() if coureur_type == 'tous' else None,
            'std': df_resampled['score']['std'].tolist() if coureur_type == 'tous' else None
        }

    return tendances


def calculate_group_trends(df_group, max_iter=100):
    """Version robuste du calcul de tendance qui évite les valeurs extrêmes"""


    # Vérifier si suffisamment de données
    if len(df_group) < 5 or len(df_group['coureur_id'].unique()) < 2:
        print(f"Données insuffisantes: {len(df_group)} points")
        # Utiliser une régression linéaire simple
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        X = df_group[['annee']].values
        y = df_group['score'].values
        model.fit(X, y)
        return {
            'avg_slope': float(model.coef_[0]),
            'avg_intercept': float(model.intercept_ - model.coef_[0] * df_group['annee'].min()),
            'group_variance': float(df_group.groupby('coureur_id')['score'].std().mean() ** 2)
        }

    try:
        # 2. Standardiser les années pour la stabilité numérique
        min_year = df_group['annee'].min()
        df_group = df_group.copy()
        df_group['year_norm'] = df_group['annee'] - min_year

        # 3. Détecter et traiter l'autocorrélation
        # Calculer une médiane par année pour réduire l'influence des valeurs extrêmes
        yearly_medians = df_group.groupby('annee')['score'].median().reset_index()

        # Régression simple sur les médianes annuelles
        X = sm.add_constant(yearly_medians['annee'])
        model_ols = sm.OLS(yearly_medians['score'], X).fit()

        # Obtenir pente et intercept des médianes
        slope = model_ols.params['annee']
        intercept = model_ols.params['const'] - slope * min_year

        # 4. Vérifier la plausibilité des résultats
        # Intervalle typique des scores observés
        expected_range = [df_group['score'].min(), df_group['score'].max()]

        # Valeurs prédites aux années min et max
        y_min = slope * df_group['annee'].min() + intercept
        y_max = slope * df_group['annee'].max() + intercept

        # Si les prédictions sont en dehors de la plage ±50% des données,
        # c'est probablement incorrect, utiliser une pente très faible
        if (y_min < expected_range[0] * 0.5 or y_min > expected_range[1] * 1.5 or
                y_max < expected_range[0] * 0.5 or y_max > expected_range[1] * 1.5):
            print(f"Valeurs prédites implausibles: y_min={y_min}, y_max={y_max}, ajustement nécessaire")
            # Utiliser une tendance quasi-plate basée sur la moyenne des scores
            slope = 0.01  # Pente très faible
            intercept = df_group['score'].mean() - slope * (df_group['annee'].min() + df_group['annee'].max()) / 2

        # 5. Calculer la variance comme mesure de l'intervalle de confiance
        residuals = df_group['score'] - (slope * df_group['annee'] + intercept)
        group_variance = np.var(residuals)

        return {
            'avg_slope': float(slope),
            'avg_intercept': float(intercept),
            'group_variance': float(group_variance),
            'is_fallback': y_min < expected_range[0] * 0.5 or y_min > expected_range[1] * 1.5
        }

    except Exception as e:
        print(f"Erreur lors du calcul de tendance: {e}")
        # Solution de repli: tendance plate à la moyenne
        return {
            'avg_slope': 0.01,
            'avg_intercept': float(df_group['score'].mean()) - 0.01 * df_group['annee'].mean(),
            'group_variance': float(df_group.groupby('coureur_id')['score'].std().mean() ** 2),
            'is_fallback': True
        }


def adjust_trend_to_fit_data(df, intercept, slope):
    """
    Ajuste l'intercept de la tendance pour s'assurer qu'elle passe au milieu des données.

    Returns:
    --------
    tuple (intercept_ajusté, slope)
    """
    # Calculer les scores prédits
    df['predicted'] = intercept + slope * df['year_norm']

    # Calculer les résidus
    df['residual'] = df['score'] - df['predicted']

    # Calculer la médiane des résidus pour avoir une mesure robuste du décalage
    median_residual = df['residual'].median()

    # Si les résidus ont une médiane significative (> 2% de l'amplitude des scores),
    # ajuster l'intercept pour décaler la ligne
    score_range = df['score'].max() - df['score'].min()
    if abs(median_residual) > 0.02 * score_range:
        # Ajuster l'intercept pour que la médiane des résidus soit proche de zéro
        adjusted_intercept = intercept + median_residual
        print(f"Ajustement de l'intercept: {intercept} → {adjusted_intercept} (médiane résidus: {median_residual})")
        return adjusted_intercept, slope

    return intercept, slope


def calculate_residual_metrics(df, slope, intercept):
    """
    Calcule des métriques sur les résidus pour évaluer la qualité de la tendance.
    """
    # Calculer les scores prédits et résidus
    predicted = intercept + slope * df['year_norm']
    residuals = df['score'] - predicted

    # Calcul de métriques
    abs_residuals = np.abs(residuals)

    return {
        'median_residual': float(np.median(residuals)),
        'mean_abs_error': float(np.mean(abs_residuals)),
        'max_abs_error': float(np.max(abs_residuals)),
        'residual_std': float(np.std(residuals)),
        'residual_range': float(np.percentile(residuals, 95) - np.percentile(residuals, 5)),
        'score_range': float(df['score'].max() - df['score'].min())
    }