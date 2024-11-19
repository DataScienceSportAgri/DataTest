from collections import defaultdict


def separer_coureurs_par_categorie(coureurs_par_categories):
    def ordre_categorie(categorie):
        ordre = {
            'CAM': 0, 'CAF': 0, 'JUM': 1, 'JUF': 1, 'ESM': 2, 'ESF': 2,
            'SEM': 3, 'SEF': 3, 'M0M': 4, 'M0F': 4, 'M1M': 5, 'M1F': 5,
            'M2M': 6, 'M2F': 6, 'M3M': 7, 'M3F': 7, 'M4M': 8, 'M4F': 8,
            'M5M': 9, 'M5F': 9, 'M6M': 10, 'M6F': 10, 'M7M': 11, 'M7F': 11,
            'M8M': 12, 'M8F': 12, 'M9M': 13, 'M9F': 13, 'M10M': 14, 'M10F': 14,
            'V1M': 4, 'V1F': 4, 'V2M': 6, 'V2F': 6, 'V3M': 8, 'V3F': 8,
            'V4M': 10, 'V4F': 10, 'V5M': 12, 'V5F': 12
        }
        return ordre.get(categorie, -1)

    def sont_categories_compatibles(cat1, cat2):
        ordre1, ordre2 = ordre_categorie(cat1), ordre_categorie(cat2)
        if ordre1 == -1 or ordre2 == -1:
            return False
        return abs(ordre1 - ordre2) <= 1

    def est_progression_logique(cat1, cat2, annees_ecart):
        ordre1, ordre2 = ordre_categorie(cat1), ordre_categorie(cat2)
        if ordre1 == -1 or ordre2 == -1:
            return False
        if annees_ecart >= 5:
            return True  # Après 5 ans, tout changement est possible
        return 0 <= ordre2 - ordre1 <= annees_ecart

    nouveaux_groupes = defaultdict(list)

    for categories, coureurs in coureurs_par_categories.items():
        categories_triees = sorted(categories)
        sous_groupes = []
        sous_groupe_courant = []
        categories_par_annee = {}

        for annee, categorie in categories_triees:
            if annee in categories_par_annee:
                if categories_par_annee[annee] != categorie:
                    # Si une catégorie différente existe déjà pour cette année, on crée un nouveau sous-groupe
                    if sous_groupe_courant:
                        sous_groupes.append(frozenset(sous_groupe_courant))
                    sous_groupe_courant = [(annee, categorie)]
                    categories_par_annee = {annee: categorie}
                continue

            categories_par_annee[annee] = categorie

            if not sous_groupe_courant:
                sous_groupe_courant.append((annee, categorie))
            else:
                annee_prec, cat_prec = sous_groupe_courant[-1]
                annees_ecart = annee - annee_prec
                if sont_categories_compatibles(cat_prec, categorie) or \
                        est_progression_logique(cat_prec, categorie, annees_ecart):
                    sous_groupe_courant.append((annee, categorie))
                else:
                    sous_groupes.append(frozenset(sous_groupe_courant))
                    sous_groupe_courant = [(annee, categorie)]

        if sous_groupe_courant:
            sous_groupes.append(frozenset(sous_groupe_courant))

        # Créer un nouveau groupe pour chaque sous-groupe
        for sous_groupe in sous_groupes:
            nouveaux_groupes[sous_groupe] = coureurs

    return nouveaux_groupes