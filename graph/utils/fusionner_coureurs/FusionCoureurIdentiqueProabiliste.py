from django.db import transaction
from django.db.models import F, Q, Count, Case, When
from django.db.models.functions import Substr, Length
from collections import defaultdict
from graph.models import Coureur, CoureurCategorie, ResultatCourse
from tqdm import tqdm
from graph.utils.fusionner_coureurs.GroupementCoureurIdentique import separer_coureurs_par_categorie
import random
import pandas as pd
import re
from .RechercheDesCoureursCoherentsParML import Optimizer
from statistics import median
import math
import uuid

import numpy as np

def calculate_std_divided_by_mean(values):
    values = np.array(values)
    std = np.std(values)
    mean = np.mean(values)
    return std / mean
def log_scale(x):
    if x <= 0.5:
        return 0.15
    elif x >= 5:
        return 0
    else:
        # Calculer la valeur logarithmique
        log_value = math.log(x / 0.5) / math.log(5 / 0.5)
        # Inverser et ajuster l'échelle
        return 0.15 * (1 - log_value)
def timeout_handler():
    raise TimeoutError("L'itération a pris trop de temps")
transaction.set_autocommit(True)
def get_dernier_suffixe(coureurs_groupe):
    suffixes = []
    for coureur in coureurs_groupe:
        match = re.search(r'\d+$', coureur.prenom)
        if match:
            suffixes.append(int(match.group()))

    return max(suffixes) if suffixes else 0

def get_coureurs_dataframe(groupe):
    prenom_base = groupe['prenom_base']
    nom = groupe['nom']
    coureurs_details = []

    coureurs_groupe = Coureur.objects.filter(
        Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$'),
        nom=nom
    ).order_by('prenom')

    for coureur in coureurs_groupe:
        categories = CoureurCategorie.objects.filter(coureur=coureur).values('annee', 'categorie')
        for cat in categories:
            coureurs_details.append([
                coureur.id,
                coureur.prenom,
                coureur.nom,
                cat['annee'],
                cat['categorie']
            ])
    df_coureurs = pd.DataFrame(coureurs_details, columns=['ID', 'Prénom', 'Nom', 'Année', 'Catégorie'])
    return df_coureurs

def create_coureurs_dataframe(coureurs_groupe):
    coureurs_details = []
    for coureur in coureurs_groupe:
        categories = CoureurCategorie.objects.filter(coureur=coureur).values('annee', 'categorie__id', 'categorie__nom')
        for cat in categories:
            coureurs_details.append({
                'ID': coureur.id,
                'Prénom': coureur.prenom,
                'Nom': coureur.nom,
                'Année': cat['annee'],
                'id_categorie': cat['categorie__id'],
                'Catégorie': cat['categorie__nom']
            })
    return pd.DataFrame(coureurs_details)

def calculate_trustability_score(normalized_nom, normalized_prenom):
    # Calculer une version ajustée de combined_value
    adjusted_nom = (normalized_nom / 25) * 0.6
    adjusted_prenom = (normalized_prenom / 50) * 0.4

    combined_value = (normalized_nom + 0.5 * normalized_prenom) * 0.6 + adjusted_nom + adjusted_prenom

    # Calculer le score final
    score = 0.7 - (np.log10(combined_value + 0.001) / np.log10(100 + 0.001)) * 0.7
    return max(0.0, min(0.7, score))

def calculate_average(dictionary):
    values = dictionary.values()
    return sum(values) / len(values) if values else 0

def fusion():
    fusion = 0
    nb_ligne_coureurcateg = 0
    nb_ligne_coureur_categ_suppr = 0
    # 1. Identifier les coureurs avec un ou plusieurs chiffres à la fin du prénom
    with transaction.atomic():
        # Calculer le nombre total de noms de famille uniques et de prénoms uniques
        # Pour les noms de famille
        occurrences_noms = Coureur.objects.values('nom').annotate(
            count=Count('nom')
        ).filter(count__gt=1).values_list('count', flat=True)

        occurrence_mediane_noms = median(occurrences_noms)

        # Pour les prénoms
        occurrences_prenoms = Coureur.objects.annotate(
            prenom_base=Substr('prenom', 1, Length('prenom') - 1)
        ).values('prenom_base').annotate(
            count=Count('prenom_base')
        ).filter(count__gt=1).values_list('count', flat=True)

        occurrence_mediane_prenoms = median(occurrences_prenoms)

        # Identifier les coureurs avec un ou plusieurs chiffres à la fin du prénom
        coureurs_numerotes = Coureur.objects.annotate(
            prenom_complet=F('prenom'),
            longueur_prenom=Length('prenom'),
            dernier_char=Substr('prenom', Length('prenom'), 1),
            avant_dernier_char=Substr('prenom', Length('prenom') - 1, 1)
        ).filter(
            Q(dernier_char__regex=r'\d') |
            Q(avant_dernier_char__regex=r'\d')
        )

        # Ajouter prenom_base et suffixe
        coureurs_numerotes = coureurs_numerotes.annotate(
            prenom_base=Substr('prenom', 1, F('longueur_prenom') - 1),
            suffixe=Substr('prenom', F('longueur_prenom'), 1)
        )

        # Grouper les coureurs par prénom (sans chiffre) et nom
        groupes = coureurs_numerotes.values('prenom_base', 'nom').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        number_of_itteration = 100
        total_groupes = groupes.count()
        batch_size = int(round(total_groupes/number_of_itteration))
        processed = 0
        print('total groupes', total_groupes)
        print_frequency = max(1, total_groupes // 20)  # Afficher environ 20 fois au total
    print('print frequency', print_frequency)# Afficher environ 20 fois au total
    e=0
    optimizer = Optimizer()
    while processed < total_groupes:


            print('processed',processed)
            # Traiter un lot de groupes
            lot_groupes = groupes[processed:processed + batch_size]
            best_dict_remake = {}
            for i, groupe in enumerate(tqdm(lot_groupes,
                                            f'lot groupes {int(round(processed / batch_size))} sur {int(round(total_groupes / batch_size))} avancement fusion')):
                # Copier les catégories du coureur original

                prenom_base = groupe['prenom_base']
                nom = groupe['nom']
                # Calculer les occurrences du nom et du prénom courants
                occurrence_nom = Coureur.objects.filter(nom=nom).count()
                occurrence_prenom = Coureur.objects.filter(
                    Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$')).count()

                # Normaliser les occurrences
                normalized_nom = occurrence_nom / occurrence_mediane_noms
                normalized_prenom = occurrence_prenom / occurrence_mediane_prenoms

                # Calculer le score de trustabilité (plus l'occurrence est forte, plus le score est faible)
                trust_name_part = calculate_trustability_score(normalized_nom, normalized_prenom)
                coureurs_par_categories = defaultdict(list)
                coureurs_groupe = Coureur.objects.filter(
                    Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$'),
                    nom=nom
                ).order_by('prenom')

                for coureur in coureurs_groupe:
                    categories = CoureurCategorie.objects.filter(coureur=coureur).values('annee', 'categorie')
                    key = frozenset((cat['annee'], cat['categorie']) for cat in categories)
                    coureurs_par_categories[key].append(coureur.id)
                df_coureurs = create_coureurs_dataframe(coureurs_groupe)
                best_dict_remake = {}
                if e % print_frequency == 0 or (0.8 > random.random() > 0.7):
                    print(f"Nombre de coureurs dans le groupe : {coureurs_groupe.count()}")
                    print(f"Normalisé nom : {normalized_nom}")
                    print(f"Normalisé prénom : {normalized_prenom}")
                    print(f"Trust_name_part : {trust_name_part}")
                # 2. Identifier les coureurs avec plusieurs entrées dans ResultatCourse
                best_dict_remake = {}
                if 35 > len(df_coureurs) > 1:
                    sous_groupes, trust_generative_part, best_dic = separer_coureurs_par_categorie(df_coureurs, optimizer)

                    if e % print_frequency == 0 or (0.24 > random.random() > 0.22):
                        print(f"Nombre de sous-groupes à fusionner : {len(sous_groupes)}")
                        print(f"Trust generative part : {trust_generative_part}")
                    sous_groupes_mis_a_jour = []
                    keys = list(best_dic.keys())
                    best_dict_remake = {}
                    for j, sous_groupe in enumerate(sous_groupes):
                        key = keys[j]
                        ids_in_groupe = sous_groupe['ID'].tolist()
                        # Vérifier si un coureur a participé à la même course plusieurs fois
                        coureurs_courses_multiples = ResultatCourse.objects.filter(
                            coureur_id__in=ids_in_groupe
                        ).values('course_id').annotate(
                            participation_count=Count('id')
                        ).filter(
                            participation_count__gt=1
                        )

                        if coureurs_courses_multiples:
                            coureurs_a_retirer = set()
                            for erreur in coureurs_courses_multiples:
                                coureurs_de_cette_course = ResultatCourse.objects.filter(
                                    course_id=erreur['course_id'],
                                    coureur_id__in=ids_in_groupe
                                ).values_list('coureur_id', flat=True)

                                coureurs_a_retirer.update(coureurs_de_cette_course)

                            # Filtrer les coureurs problématiques du sous-groupe
                            ids_valides = [id for id in ids_in_groupe if id not in coureurs_a_retirer]
                            sous_groupe_mis_a_jour = sous_groupe[sous_groupe['ID'].isin(ids_valides)]

                            if not sous_groupe_mis_a_jour.empty:
                                unique = str(uuid.uuid4())
                                best_dict_remake[unique] = best_dic[key]
                                sous_groupes_mis_a_jour.append(sous_groupe_mis_a_jour)
                        else:
                            unique = str(uuid.uuid4())
                            best_dict_remake[unique] = best_dic[key]
                            sous_groupes_mis_a_jour.append(sous_groupe)

                    if e % print_frequency == 0 or (0.56 > random.random() > 0.55):
                        print(f"  Coureurs restants après correction des erreurs: {sous_groupes_mis_a_jour}")
                    distances_de_course = []
                    new_keys = list(best_dict_remake.keys())
                    a=0
                    for sous_groupe_mis_a_jour in sous_groupes_mis_a_jour:
                        ids_valides = sous_groupe_mis_a_jour['ID'].tolist()
                        if len(ids_valides) > 1:
                            coureur_principal_id = ids_valides[0]
                            try:
                                coureur_principal = Coureur.objects.get(id=coureur_principal_id)
                            except:
                                continue
                            # Récupérer les distances de course pour tous les coureurs du sous-groupe
                            resultats = ResultatCourse.objects.filter(coureur_id__in=ids_valides).select_related(
                                'course')

                            for resultat in resultats:
                                distances_de_course.append(resultat.course.distance)

                            #récupérer la distance de course pour chaque coureur à fusionner et du coureur principal, via le Résultat course et la table course

                            # Récupérer les entrées CoureurCategorie pour les coureurs à fusionner
                            coureur_categories = CoureurCategorie.objects.filter(coureur_id__in=ids_valides)

                            # Créer un DataFrame à partir des données récupérées
                            df = pd.DataFrame(
                                list(coureur_categories.values('id', 'coureur_id', 'categorie_id', 'annee')))
                            print('df',df)
                            unique_df = df.drop_duplicates(subset=['annee', 'categorie_id'], keep='first')

                            duplicates = df[~df['id'].isin(unique_df['id'])]

                            nb_ligne_coureur_categ_suppr += len(duplicates)
                            ids_to_delete = df['id'].tolist()
                            with transaction.atomic():

                                CoureurCategorie.objects.filter(id__in=ids_to_delete).delete()
                            with transaction.atomic():
                                # Au lieu de supprimer et recréer, utilisez update_or_create
                                for _, row in unique_df.iterrows():
                                    CoureurCategorie.objects.update_or_create(
                                        id=row['id'],
                                        defaults={
                                            'coureur_id': coureur_principal_id,
                                            'categorie_id': row['categorie_id'],
                                            'annee': row['annee']
                                        }
                                    )
                                    nb_ligne_coureurcateg += 1



                                for coureur_id in ids_valides[1:]:
                                    if coureur_id != coureur_principal_id:
                                        # Mettre à jour les résultats de course
                                        ResultatCourse.objects.filter(coureur_id=coureur_id).update(
                                            coureur_id=coureur_principal_id)
                                        # Supprimer le coureur fusionné
                                        Coureur.objects.filter(id=coureur_id).delete()
                                        fusion += 1

                                # récupérer la liste des distances de tout les coureurs
                                #calculer un écart-type pondéré par la division par la moyenne.
                                #utiliser cet écart-type pondéré pour ajouter au score de viabilité, plus l'écart type est grand
                                #plus le score de viabilité diminue
                                #ajouter le score de viabilité au coureur principal dans la colonne 'coureur principal' sur sql.
                                # Calculer l'écart-type pondéré
                                trust_categ_change_part_score = best_dict_remake[new_keys[a]]
                                normalized_std = calculate_std_divided_by_mean(distances_de_course)
                                trust_distance_part = log_scale(normalized_std)
                                trustability_score = trust_name_part + trust_distance_part + trust_generative_part + trust_categ_change_part_score
                                # Mettre à jour le score de viabilité du coureur principal
                                coureur_principal = Coureur.objects.get(id=coureur_principal_id)
                                coureur_principal.score_de_viabilite = trustability_score
                                coureur_principal.save()
                            a+=1



                            if e % print_frequency == 0 or (0.46 > random.random() > 0.47):
                                print(f"  Fusion effectuée dans le sous-groupe {j + 1}:")
                                print(f"    Coureur principal : {coureur_principal.prenom} {coureur_principal.nom}")
                                print(f"    Nombre de coureurs fusionnés : {len(sous_groupe_mis_a_jour) - 1}")
                                print('fusion :', fusion)
                                print('trustability_score :', trustability_score)
                                print('nbligne coureurcateg :', nb_ligne_coureurcateg)
                                print('nbligne coureurcateg supr:', nb_ligne_coureur_categ_suppr)
                                print('teust categorie change part',trust_categ_change_part_score)
                                try:
                                    print('optimizer super patterns',optimizer.super_patterns)
                                    print('optimizer catalog', optimizer.get_all_patterns())
                                except:
                                    print('no patterns')
                                print('e', e)
                            e += 1
                        e+=1
                        processed += 1


            print(f'nouveau {int(round(processed / batch_size))} % terminé')
    print('fusion terminé')