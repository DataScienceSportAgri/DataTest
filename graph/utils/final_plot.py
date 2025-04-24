# utils.py
import numpy as np
import pandas as pd
from django.db.models import Q
from graph.models import Coureur, ResultatCourse
import json
from scipy import stats
import re
import statsmodels.api as sm
import numpy as np
from sklearn.linear_model import LinearRegression, TheilSenRegressor
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


def filter_extreme_trend_runners(df_group, percentile_cut=10):
    """
    Filtre les coureurs ayant les pentes les plus extrêmes.

    Parameters:
    -----------
    df_group : DataFrame
        Données des coureurs avec 'coureur_id', 'annee', 'score'
    percentile_cut : int
        Pourcentage des coureurs avec pentes extrêmes à éliminer (de chaque côté)

    Returns:
    --------
    DataFrame
        Données filtrées sans les coureurs aux pentes extrêmes
    """
    # Calculer la pente pour chaque coureur
    slopes = []
    for coureur_id, c_df in df_group.groupby('coureur_id'):
        if len(c_df) < 3:  # Besoin d'au moins 3 points pour une pente fiable
            continue

        c_df = c_df.sort_values('annee')
        X = c_df[['annee']].values
        y = c_df['score'].values

        try:
            # Utiliser TheilSenRegressor pour une estimation robuste de la pente
            model = TheilSenRegressor().fit(X, y)
            slopes.append((coureur_id, model.coef_[0]))
        except:
            # En cas d'erreur, conserver le coureur
            continue

    # Trier les coureurs par pente
    slopes.sort(key=lambda x: x[1])

    # Calculer les indices des coureurs à conserver
    n = len(slopes)
    lower_cut = int(n * percentile_cut / 100)
    upper_cut = n - lower_cut

    # Extraire les IDs des coureurs à conserver (exclure les extrêmes)
    keep_ids = [s[0] for s in slopes[lower_cut:upper_cut]]

    # Filtrer le DataFrame
    return df_group[df_group['coureur_id'].isin(keep_ids)]


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
        coureur_unique = Coureur.objects.filter(score_de_viabilite__gt=0.3)
        print('len de coureur unique',len(coureur_unique))
        return coureur_unique
    elif coureur_type == 'tous':
        random_coureurs = Coureur.objects.order_by('?')[:10000]
        return random_coureurs
    raise ValueError("Type de coureur invalide")


def calculate_percentile_groups(scores, distribution_type='quartiles'):
    """
    Retourne un tuple contenant :
    - Series pandas avec les groupes (labels CSS-safe)
    - Dictionnaire de correspondance {label_safe: label_affichage}
    """
    scores = pd.Series(scores)

    # Configuration des découpages
    if distribution_type == 'quartiles':
        quantiles = [0, 0.25, 0.5, 0.75, 1.0]
        labels_affichage = ['0-25%', '25-50%', '50-75%', '75-100%']
        labels_safe = ['q1', 'q2', 'q3', 'q4']

    elif distribution_type == 'top35':
        quantiles = np.linspace(0.65, 1.0, 8)  # 7 tranches de 5% dans le top 35%
        labels_affichage = [f'{int(65 + i * 5)}-{70 + i * 5}%' for i in range(7)]
        labels_safe = [f'top35_{i + 1}' for i in range(7)]

    elif distribution_type == 'bottom80':
        quantiles = np.linspace(0.0, 0.8, 9)  # 8 tranches de 10% dans le bottom 80%
        labels_affichage = [f'{i * 10}-{(i + 1) * 10}%' for i in range(8)]
        labels_safe = [f'bot80_{i + 1}' for i in range(8)]

    else:
        raise ValueError(f"Type de distribution non supporté : {distribution_type}")

    # Gestion des cas extrêmes (toutes valeurs identiques)
    if scores.nunique() == 1:
        groupes = pd.Series(labels_safe[0], index=scores.index)
        label_map = {labels_safe[0]: labels_affichage[0]}
        return groupes, label_map

    # Découpage avec gestion automatique des doublons
    try:
        groupes = pd.qcut(
            scores,
            q=quantiles,
            labels=labels_safe,
            duplicates='drop'  # Fusionne les intervalles identiques
        )

        # Création du mapping des labels
        unique_groups = groupes.cat.categories
        label_map = {
            group: labels_affichage[i]
            for i, group in enumerate(unique_groups)
        }

    except Exception as e:
        print(f"Erreur lors du découpage : {e}")
        groupes = pd.Series(['erreur'] * len(scores), index=scores.index)
        label_map = {'erreur': 'Erreur de découpage'}

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
        print('test df coureur',df)
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
            # 2. Sélectionner les 30 coureurs avec le plus de points dans ce groupe
            top_coureurs_df = get_coureurs_by_count(group_df_processed, group_col='groupe', n=30)
            groupe_safe = generate_safe_label(group_df_processed)

            # 3. Ajouter toutes les séries individuelles sélectionnées
            for coureur_id, coureur_df in top_coureurs_df.groupby('coureur_id'):
                values = [
                    {"date": int(annee), "score": float(score), "coureur_id": coureur_id,
                     "prenom_marsien": prenom, "nom_marsien": nom}
                    for annee, score, coureur_id, nom, prenom in zip(
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
                    "score":score_type,
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
                    "score": score_type,
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
                    "score": score_type,
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


def calculate_group_trends(df_group, max_iter=10000, percentile_cut=10):
    """Version améliorée du calcul de tendance avec meilleure gestion des cas extrêmes"""
    # Étape 0: Filtrer les coureurs avec tendances extrêmes
    df_filtered = filter_extreme_trend_runners(df_group, percentile_cut=percentile_cut)

    # Vérification post-filtrage
    if len(df_filtered) < 5 or len(df_filtered['coureur_id'].unique()) < 2:
        df_filtered = df_group.copy()
        print("Utilisation des données originales après filtrage infructueux")

    # 1. Calcul des pentes individuelles pondérées
    individual_slopes = []
    weights = []
    valid_coureurs = 0

    for coureur_id, group in df_filtered.groupby('coureur_id'):
        if len(group) < 2:
            continue  # Pas assez de points pour calculer une pente

        X = group[['annee']].values
        y = group['score'].values

        try:
            model = LinearRegression().fit(X, y)
            slope = model.coef_[0]
            individual_slopes.append(slope)
            weights.append(len(group))  # Poids = nombre de points
            valid_coureurs += 1
        except:
            continue

    # 2. Calcul de la pente moyenne pondérée
    if valid_coureurs >= 3:  # Au moins 3 coureurs valides
        avg_slope = np.average(individual_slopes, weights=weights)
        mean_year = df_filtered['annee'].mean()
        mean_score = df_filtered['score'].mean()
        avg_intercept = mean_score - avg_slope * mean_year
    else:
        avg_slope = None

    # 3. Régression robuste sur l'ensemble des points
    try:
        robust_model = TheilSenRegressor(max_iter=max_iter).fit(df_filtered[['annee']], df_filtered['score'])
        robust_slope = robust_model.coef_[0]
        robust_intercept = robust_model.intercept_
    except:
        robust_slope = 0.0
        robust_intercept = df_filtered['score'].mean()

    # 4. Combinaison des deux méthodes (50/50)
    if avg_slope is not None and not np.isnan(avg_slope):
        final_slope = 0.5 * avg_slope + 0.5 * robust_slope
        final_intercept = 0.5 * avg_intercept + 0.5 * robust_intercept
        method_used = "combined_individual_and_robust"
    else:
        final_slope = robust_slope
        final_intercept = robust_intercept
        method_used = "robust_fallback"

    # 5. Calcul de la variance résiduelle
    residuals = df_filtered['score'] - (final_slope * df_filtered['annee'] + final_intercept)
    group_variance = np.var(residuals)

    return {
        'avg_slope': float(final_slope),
        'avg_intercept': float(final_intercept),
        'group_variance': float(group_variance),
        'method': method_used,
        'individual_slopes_count': valid_coureurs
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