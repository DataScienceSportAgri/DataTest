from django.db import transaction
from django.db.models import F, Q, Count, Max
from django.db.models.functions import Substr, Length
from collections import defaultdict
from ..models import Coureur, CoureurCategorie, ResultatCourse
import re
from tqdm import tqdm
from .test_fusion_coureurs import separer_coureurs_par_categorie
import random

transaction.set_autocommit(True)
def get_dernier_suffixe(coureurs_groupe):
    suffixes = []
    for coureur in coureurs_groupe:
        match = re.search(r'\d+$', coureur.prenom)
        if match:
            suffixes.append(int(match.group()))

    return max(suffixes) if suffixes else 0

def fusionner_et_defusionner_coureurs():
    fusion = 0
    defusion = 0
    # 1. Identifier les coureurs avec un ou plusieurs chiffres à la fin du prénom
    with transaction.atomic():
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
        processed = 1981
        print_frequency = max(1, total_groupes // 20)  # Afficher environ 20 fois au total
    while processed < total_groupes:
        with transaction.atomic():
            # Traiter un lot de groupes
            lot_groupes = groupes[processed:processed + batch_size]
            for i, groupe in enumerate(tqdm(lot_groupes, f'lot groupes {int(round(processed/batch_size))} sur {int(round(total_groupes/batch_size))} avancement desfusion')):
                prenom_base = groupe['prenom_base']
                nom = groupe['nom']
                if i % print_frequency == 0 or random.random() < 0.05:  # Afficher régulièrement ou aléatoirement
                    print(f"\nTraitement du groupe : {prenom_base} {nom}")

                # Récupérer tous les coureurs de ce groupe
                coureurs_groupe = Coureur.objects.filter(
                    Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$'),
                    nom=nom
                ).order_by('prenom')
                if i % print_frequency == 0 or random.random() < 0.05:
                    print(f"Nombre de coureurs dans le groupe : {coureurs_groupe.count()}")
                # 2. Identifier les coureurs avec plusieurs entrées dans ResultatCourse
                coureurs_multiples_courses = ResultatCourse.objects.filter(
                    coureur__in=coureurs_groupe
                ).values('coureur').annotate(
                    count=Count('id')
                ).filter(count__gt=1).values_list('coureur_id', flat=True)

                # Séparer les coureurs en deux groupes
                coureurs_a_defusionner = coureurs_groupe.filter(id__in=coureurs_multiples_courses)
                coureurs_a_fusionner = coureurs_groupe.exclude(id__in=coureurs_multiples_courses)
                # Fusionner les coureurs qui peuvent l'être
                # Obtenir tous les coureurs de ce groupe

                # 3. Récupérer le dernier numéro de suffixe
                dernier_suffixe = get_dernier_suffixe(coureurs_groupe)
                # 4. Défusionner les coureurs avec plusieurs entrées
                for coureur in coureurs_a_defusionner:
                    resultats_course = ResultatCourse.objects.filter(coureur=coureur)
                    for e, resultat in enumerate(resultats_course[1:], start=1):
                        dernier_suffixe += 1
                        nouveau_prenom = f"{prenom_base}{dernier_suffixe}"
                        nouveau_coureur = Coureur.objects.create(
                            prenom=nouveau_prenom,
                            nom=coureur.nom
                        )

                        resultat.coureur = nouveau_coureur
                        resultat.save()
                        defusion +=1

        with transaction.atomic():
            # Traiter un lot de groupes
            lot_groupes = groupes[processed:processed + batch_size]
            for i, groupe in enumerate(tqdm(lot_groupes,
                                            f'lot groupes {int(round(processed / batch_size))} sur {int(round(total_groupes / batch_size))} avancement fusion')):
                # Copier les catégories du coureur original
                prenom_base = groupe['prenom_base']
                nom = groupe['nom']
                coureurs_par_categories = defaultdict(list)
                coureurs_groupe = Coureur.objects.filter(
                    Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$'),
                    nom=nom
                ).order_by('prenom')

                for coureur in coureurs_groupe:
                    categories = CoureurCategorie.objects.filter(coureur=coureur).values('annee', 'categorie')
                    key = frozenset((cat['annee'], cat['categorie']) for cat in categories)
                    coureurs_par_categories[key].append(coureur.id)  # Ajoutez .id ici
                if i % print_frequency == 0 or random.random() < 0.05:
                    print(f"Nombre de coureurs dans le groupe : {coureurs_groupe.count()}")
                # 2. Identifier les coureurs avec plusieurs entrées dans ResultatCourse

                coureurs_a_fusionner = coureurs_groupe
                if coureurs_a_fusionner.count() > 1:

                    sous_groupes = separer_coureurs_par_categorie(coureurs_par_categories)

                    if i % print_frequency == 0 or random.random() < 0.05:
                        print(f"Nombre de sous-groupes à fusionner : {len(sous_groupes)}")
                    for j, (id, sous_groupe) in enumerate(sous_groupes.items()):

                        # Convertir sous_groupe en liste d'IDs si ce n'est pas déjà le cas
                        # Vérifier si un coureur a participé à la même course plusieurs fois
                        # Effectuez la requête et le traitement en une seule étape
                        coureurs_courses_multiples = ResultatCourse.objects.filter(
                            coureur_id__in=sous_groupe
                        ).values('course_id').annotate(
                            participation_count=Count('id')
                        ).filter(
                            participation_count__gt=1
                        )

                        if coureurs_courses_multiples:
                            if i % print_frequency == 0 or random.random() < 0.05:
                                print(f"Erreur détectée dans le sous-groupe {j + 1}:")

                            coureurs_a_retirer = set()
                            for erreur in coureurs_courses_multiples:
                                # Obtenir tous les coureurs qui ont participé à cette course
                                coureurs_de_cette_course = ResultatCourse.objects.filter(
                                    course_id=erreur['course_id'],
                                    coureur_id__in=sous_groupe
                                ).values_list('coureur_id', flat=True)

                                coureurs_a_retirer.update(coureurs_de_cette_course)

                                if i % print_frequency == 0 or random.random() < 0.05:
                                    print(
                                        f"  Course ID {erreur['course_id']} a {erreur['participation_count']} participations multiples"
                                    )

                            # Retirer les coureurs problématiques du sous-groupe
                            sous_groupe = [id for id in sous_groupe if id not in coureurs_a_retirer]

                            if i % print_frequency == 0 or random.random() < 0.05:
                                print(f"  Coureurs restants après correction des erreurs: {sous_groupe}")




                        if len(sous_groupe) > 1:
                            # Prendre le premier coureur comme coureur principal
                            coureur_principal_id = sous_groupe[0]
                            coureur_principal = Coureur.objects.get(id=coureur_principal_id)



                            # Itérer sur les autres coureurs du sous-groupe
                            for coureur_id in sous_groupe[1:]:
                                # Identifier les doublons de catégorie et année
                                doublons = CoureurCategorie.objects.filter(coureur_id__in=sous_groupe) \
                                    .values('categorie_id', 'annee') \
                                    .annotate(count=Count('id')) \
                                    .filter(count__gt=1)

                                # Supprimer les doublons, en gardant l'entrée du coureur principal
                                for doublon in doublons:
                                    CoureurCategorie.objects.filter(
                                        coureur_id__in=sous_groupe,
                                        categorie_id=doublon['categorie_id'],
                                        annee=doublon['annee']
                                    ).exclude(coureur_id=coureur_principal_id).delete()

                                # Mettre à jour les résultats de course
                                ResultatCourse.objects.filter(coureur_id=coureur_id).update(
                                    coureur_id=coureur_principal_id)

                                # Supprimer le coureur fusionné
                                Coureur.objects.filter(id=coureur_id).delete()
                                fusion += 1




                            if i % print_frequency == 0 or random.random() < 0.05:
                                print(f"  Fusion effectuée dans le sous-groupe {j + 1}:")
                                print(f"    Coureur principal : {coureur_principal.prenom} {coureur_principal.nom}")
                                print(f"    Nombre de coureurs fusionnés : {len(sous_groupe) - 1}")
                            if len(sous_groupe)>2:
                                print(f"    Nombre de coureurs fusionnés : {len(sous_groupe) - 1}")
            print(f'defusion totale = {defusion}, fusion totale  = {fusion}.')
            processed += len(lot_groupes)
            print(f"Processus de fusion et défusion des coureurs terminé groupe {processed} sur {total_groupes}.")
        print("Processus de fusion et défusion des coureurs entièrement terminé.")