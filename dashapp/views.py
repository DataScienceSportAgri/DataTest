from django.urls import reverse

from django.db import transaction
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from DataTest import settings
from .ElasticNet_models import vectorize_data, load_filtered_data, load_points_data, train_ElasticNet_model, predict_elasticnet
from .models import *
import json
from dashapp.utils.utils import *
from django.middleware.csrf import get_token, logger
from django.core.cache import cache
from shapely.geometry import Point

def dash_view(request):
    # Créer un dictionnaire Python (pas de conversion JSON)
    context = {
        'dash_args': {
            'csrf-store': {'data': get_token(request)}, # ID du composant + propriété
            'dummy': {'value': "test"} # Exemple supplémentaire
        }
    }
    return render(request, 'dashapp/dash_embed.html', context)

def simple_view(request):
    # Exemple d'une vue simple qui retourne une réponse HTTP
    return HttpResponse("Bienvenue sur l'application Dash intégrée à Django !")


@csrf_exempt
def process_ml_pipeline(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            training_config = data.get('training', {})
            prediction_config = data.get('prediction', {})
            other_values = data.get('othervalues', {})
            # Validation des configurations
            print('training_congig',training_config)
            # Chargement des données d'entraînement
            if training_config['mode'] == 'points':
                df_train = load_points_data(
                    session_id=request.session.session_key,
                    parcelles_dates_dict=training_config['parcelles_dates_dict'],
                    indices=training_config['indices'],
                    points_client=training_config.get('points', []),
                )
            else:

                df_train = load_filtered_data(
                    country_codes=training_config['country_codes'],
                    parcelles_dict_date=training_config['parcelles_dates_dict'],
                    indices=training_config['indices'],
                    min_rendement=training_config['filters'].get('rendement_min', 0),
                    max_rendement=training_config['filters'].get('rendement_max', 100),
                    min_indice=training_config['filters'].get('indice_min', 0),
                    max_indice=training_config['filters'].get('indice_max', 100)
                )

            # Entraînement du modèle
            vectors_train = vectorize_data(data=df_train, buffer_distance=other_values['macrobuffer'], microbuffer = other_values['microbuffer'])

            model = train_ElasticNet_model(vectors_train,centroidvalue=other_values['centroidvalue'],arrivalvalue=other_values['arrivalvalue'],comb=other_values['comb'])
            print('features',model['features'])

            # Chargement des données de prédiction
            if prediction_config['mode'] == 'points':
                df_pred = load_points_data(
                    session_id=request.session.session_key,
                    parcelles_dates_dict=training_config['parcelles_dates_dict'],
                    indices=training_config['indices'],
                    points_client=prediction_config.get('points', []),
                )
            else:
                df_pred = load_filtered_data(
                    country_codes=prediction_config['country_codes'],
                    parcelles_dict_date=prediction_config['parcelles'],
                    indices=training_config['indices'],
                    min_rendement=training_config['filters'].get('rendement_min', 0),
                    max_rendement=training_config['filters'].get('rendement_max', 100),
                    min_indice=training_config['filters'].get('indice_min', 0),
                    max_indice=training_config['filters'].get('indice_max', 100)
                )

            # Prédictions
            predictions = predict_elasticnet(model, df_pred[training_config['indices']])

            # Génération des IDs de résultat
            train_result_id = str(uuid.uuid4())
            pred_result_id = str(uuid.uuid4())

            # Stockage des résultats
            cache.set_many({
                 f'ml_train_{train_result_id}': {
                     'r2': model['r2'],
                     'rmse': model['cv_rmse'],
                     'features': model['feature_importance'],
                     'plot_data': model.get('3d_plot')
                 },
                 f'ml_pred_{pred_result_id}': predictions
             }, timeout=3600)
            # Génération de l'URL avec reverse()

            return JsonResponse({
                'status': 'success',
                'train_result_id': train_result_id,
                'pred_result_id': pred_result_id,
                'redirect_url': reverse(
                'dashapp:ml_results',
                args=[train_result_id, pred_result_id]
            )  # Ajout du préfixe si nécessaire
            })

        except Exception as e:
            logger.exception("Erreur globale du pipeline")
            return JsonResponse({'error': str(e)}, status=500)


def ml_results_view(request, train_result_id, pred_result_id):
    train_data = cache.get(f'ml_train_{train_result_id}')
    pred_data = cache.get(f'ml_pred_{pred_result_id}')

    if not train_data or not pred_data:
        return render(request, 'error.html', {'message': 'Résultats expirés'})

    return render(request, 'dashapp/ml_results.html', {
        'training': {
            'r2': train_data['r2'],
            'rmse': train_data['rmse'],
            'features': train_data['features']
        },
        'prediction': {
            'stats': pred_data['stats'],
            'sample': pred_data['sample_data']
        },
        'plot_data': train_data['plot_data']
    })


@csrf_exempt
def save_points(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            raw_points = data.get('points', [])
            base_path = os.path.join(settings.BASE_DIR, "dashapp", "saved_parcelle_for_dash")

            print(f"\n=== REQUÊTE REÇUE ===")
            print(f"Session ID: {session_id}")
            print(f"Nombre de points reçus: {len(raw_points)}")

            if not session_id:
                print("!!! ERREUR: Session ID manquant")
                return JsonResponse({'error': 'Session ID requis'}, status=400)

            # Étape 1: Extraction des combinaisons uniques
            unique_combinations = {
                (p['country_code'], p['parcelle'])
                for p in raw_points
                if 'country_code' in p and 'parcelle' in p
            }
            print('combinaisons unique', unique_combinations)
            print(f"\nCombinaisons uniques trouvées: {len(unique_combinations)}")
            for i, (country, parcelle) in enumerate(unique_combinations, 1):
                print(f"{i}. {country}/{parcelle}")

            # Étape 2: Chargement des dataframes
            buffered_dfs = {}
            for country, parcelle in unique_combinations:
                try:
                    file_path = os.path.join(base_path, country, str(parcelle), "utils", f"{str(parcelle)}_filtered.pkl")
                    print(f"\nTentative de chargement: {file_path}")

                    if not os.path.exists(file_path):
                        print("Fichier non trouvé")
                        continue

                    df = pd.read_pickle(file_path)
                    print(f"DataFrame chargé - {len(df)} points")

                    geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
                    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326").to_crs(epsg=32631)
                    gdf['buffer'] = gdf.geometry.buffer(4)

                    buffered_dfs[(country, parcelle)] = gdf
                    print(f"Buffer de 4m appliqué - {len(gdf)} geometries")

                except Exception as e:
                    print(f"!!! ERREUR: {str(e)}")
                    continue

            # Étape 3: Traitement des points
            saved_count = 0
            batch_size = 100
            print("\n=== TRAITEMENT DES POINTS ===")

            with transaction.atomic():
                for idx, point in enumerate(raw_points, 1):
                    try:
                        # Validation du champ training
                        is_training = point.get('training', False)
                        country = point['country_code']
                        parcelle = point['parcelle']
                        lat = float(point['lat'])
                        lon = float(point['lon'])
                        print(f"\nPoint {idx}/{len(raw_points)}: {country}/{parcelle} ({lat}, {lon})")

                        gdf = buffered_dfs.get((country, parcelle))
                        if gdf is None or gdf.empty:  # Vérification explicite
                            print("Aucun DataFrame disponible")
                            continue

                        point_utm = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(gdf.crs)[0]
                        print(f"Coordonnées UTM: {point_utm}")
                        if parcelle == 'Boulinsard':
                            index = '2021-03-01'
                        else:
                            index = 'date_1'
                        match = gdf[gdf['buffer'].contains(point_utm)]
                        SelectedPoint.objects.update_or_create(
                            session_id=session_id,
                            country_code=country,
                            parcelle=parcelle,
                            latitude=lat,
                            longitude=lon,
                            training=is_training,  # Inclus dans la
                            defaults={
                                'dataframe_index': 0,
                                'rendement': match.iloc[0].Rendement,
                                'ndvi': match.iloc[0].get('NDVI')
                            }
                        )
                        saved_count += 1

                        if saved_count % batch_size == 0:
                            transaction.commit()
                            print(f"== Commit transaction #{saved_count // batch_size} ==")

                    except Exception as e:
                        print(f"!!! ERREUR sur le point {idx}: {str(e)}")
                        continue

            print(f"\n=== RÉSULTATS FINAUX ===")
            print(f"Points sauvegardés: {saved_count}/{len(raw_points)}")
            print(f"Parcelles valides: {len(buffered_dfs)}")

            return JsonResponse({
                'count': saved_count,
                'valid_parcelles': len(buffered_dfs)
            })

        except json.JSONDecodeError:
            print("!!! ERREUR: JSON invalide")
            return JsonResponse({'error': 'Format JSON invalide'}, status=400)
        except Exception as e:
            print(f"!!! ERREUR GLOBALE: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

def get_points(request):
    session_id = request.GET.get('session_id')
    country = request.GET.get('country')
    parcelle = request.GET.get('parcelle')

    query = SelectedPoint.objects.filter(session_id=session_id)

    if country:
        query = query.filter(country_code=country)

    if parcelle:
        query = query.filter(parcelle=parcelle)

    points = list(query.values())

    return JsonResponse({'points': points})