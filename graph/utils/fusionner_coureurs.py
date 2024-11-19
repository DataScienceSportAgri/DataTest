from django.db import transaction
from django.db.models import Count, Q, F
from collections import defaultdict
from django.db.models.functions import Substr, Length
from ..models import Coureur, CoureurCategorie, ResultatCourse
import re
from tqdm import tqdm

def fusionner_coureurs():
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

        for groupe in tqdm(groupes, desc="Traitement des groupes"):
            prenom_base = groupe['prenom_base']
            nom = groupe['nom']

            # Obtenir tous les coureurs de ce groupe
            coureurs = Coureur.objects.filter(
                Q(prenom=prenom_base) | Q(prenom__startswith=prenom_base, prenom__regex=r'\d$'),
                nom=nom
            ).order_by('prenom')

            # Créer un dictionnaire pour grouper les coureurs par leurs catégories par année
            coureurs_par_categories = defaultdict(list)

            for coureur in coureurs:
                categories = CoureurCategorie.objects.filter(coureur=coureur).values('annee', 'categorie')
                key = frozenset((cat['annee'], cat['categorie']) for cat in categories)
                coureurs_par_categories[key].append(coureur)

            # Traiter chaque sous-groupe séparément
            for sous_groupe in coureurs_par_categories.values():
                if len(sous_groupe) > 1:
                    # Vérifier si les coureurs ont participé aux mêmes courses
                    courses_par_coureur = defaultdict(set)
                    for coureur in sous_groupe:
                        courses = ResultatCourse.objects.filter(coureur=coureur).values_list('course_id', flat=True)
                        courses_par_coureur[coureur.id] = set(courses)

                    # Trouver les coureurs qui n'ont pas de courses en commun
                    coureurs_a_fusionner = []
                    for i, coureur in enumerate(sous_groupe):
                        peut_etre_fusionne = True
                        for autre_coureur in sous_groupe[i + 1:]:
                            if courses_par_coureur[coureur.id] & courses_par_coureur[autre_coureur.id]:
                                peut_etre_fusionne = False
                                break
                        if peut_etre_fusionne:
                            coureurs_a_fusionner.append(coureur)

                    if len(coureurs_a_fusionner) > 1:
                        # Procéder à la fusion pour les coureurs qui peuvent être fusionnés
                        try:
                            coureur_principal = min(
                                coureurs_a_fusionner,
                                key=lambda x: int(x.prenom[-1]) if x.prenom[-1].isdigit() else 0
                            )
                        except:
                            break

                        # Mettre à jour les résultats de course
                        ResultatCourse.objects.filter(
                            coureur__in=coureurs_a_fusionner
                        ).exclude(
                            coureur=coureur_principal
                        ).update(coureur=coureur_principal)

                        # Mettre à jour les entrées de CoureurCategorie
                        CoureurCategorie.objects.filter(
                            coureur__in=coureurs_a_fusionner
                        ).exclude(
                            coureur=coureur_principal
                        ).delete()  # Supprime les entrées au lieu de les mettre à jour

                        # Supprimer les coureurs fusionnés
                        Coureur.objects.filter(id__in=[c.id for c in coureurs_a_fusionner]).exclude(
                            id=coureur_principal.id).delete()

                        print(
                            f"Fusion effectuée pour un sous-groupe de {coureur_principal.prenom} {coureur_principal.nom}")
                    else:
                        print(
                            f"Pas de fusion possible pour {sous_groupe[0].prenom} {sous_groupe[0].nom} : courses en commun détectées")
                else:
                    print(
                        f"Pas de fusion nécessaire pour un coureur unique de {sous_groupe[0].prenom} {sous_groupe[0].nom}")

        print("Processus de fusion des coureurs terminé.")