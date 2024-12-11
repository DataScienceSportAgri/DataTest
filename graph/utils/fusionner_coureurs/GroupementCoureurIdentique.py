from collections import defaultdict
import pandas as pd
import uuid
import random
from threading import Timer
import time


def supprimer_ids_communs(dataframes):
    # Concaténer tous les DataFrames dans un seul DataFrame
    try:
        concatenated = pd.concat(dataframes, ignore_index=True)
    except:
        return []

    # Trouver les IDs uniques : garder la première occurrence de chaque ID
    filtered = concatenated.drop_duplicates(subset=['ID'], keep='first')

    # Filtrer uniquement les DataFrames initiaux avec les ID restants
    ids_restants = set(filtered['ID'])
    result = []
    for df in dataframes:
        df_filtre = df[df['ID'].isin(ids_restants)]
        if not df_filtre.empty:
            result.append(df_filtre)  # Ajouter uniquement si le DataFrame n'est pas vide

    return result

def scale_values(super_dic, max_value):
    if max_value >= 50:
        scale_max = 0.1
    elif max_value >= 10:
        scale_max = 0.09
    elif max_value >= 3:
        scale_max = 0.05
    elif max_value >=1:
        scale_max = 0.01
    else:
        scaled_dic = {}
        for key, sub_dict in super_dic.items():
            scaled_dic[key] = {}
            for sub_key, value in sub_dict.items():
                scaled_dic[key][sub_key] = 0
        return scaled_dic

    scaled_dic = {}
    for key, sub_dict in super_dic.items():
        scaled_dic[key] = {}
        for sub_key, value in sub_dict.items():
            scaled_value = max(0, scale_max * (1 - value / max_value))
            scaled_dic[key][sub_key] = min(scale_max, scaled_value)

    return scaled_dic



def separer_coureurs_par_categorie(coureurs_par_categories, optimizer):
    trust_generative_part = 0.1
    cat_artificielle = {
        'CAM': ['A'], 'CAF': ['A'], 'JUM': ['B'], 'JUF': ['B'], 'ESM': ['C'], 'ESF': ['C'],
        'SEM': ['D'], 'SEF': ['D'], 'M0M': ['D'], 'M0F': ['D'], 'M1M': ['E'], 'M1F': ['E'],
        'M2M': ['F'], 'M2F': ['F'], 'M3M': ['G'], 'M3F': ['G'], 'M4M': ['H'], 'M4F': ['H'],
        'M5M': ['I'], 'M5F': ['I'], 'M6M': ['J'], 'M6F': ['J'], 'M7M': ['K'], 'M7F': ['K'],
        'M8M': ['L'], 'M8F': ['L'], 'M9M': ['M'], 'M9F': ['M'], 'M10M': ['N'], 'M10F': ['N'],
        'V1M': ['E', 'F'], 'V1F': ['E', 'F'], 'V2M': ['G', 'H'], 'V2F': ['G', 'H'], 'V3M': ['I', 'J'],
        'V3F': ['I', 'J'],
        'V4M': ['K', 'L'], 'V4F': ['K', 'L'], 'V5M': ['M', 'N'], 'V5F': ['M', 'N']
    }
    def exclure_categories_non_existantes(df_coureurs):
        # Filtrer les catégories pour ne garder que celles existant dans le dictionnaire
        categories_valides = set(cat_artificielle.keys())
        df_filtre = df_coureurs[df_coureurs['Catégorie'].isin(categories_valides)]
        return df_filtre
    def ordre_categorie(categorie, typ='ordre'):
        ordre = {
            'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,'J':10,'K':11,'L':12,'M':13,'N':14
            }
        if categorie not in cat_artificielle:
            return None
        if typ == 'check':
            return [ordre[cat] for cat in cat_artificielle[categorie]]
        elif typ == 'ordre':
            return min(ordre[cat] for cat in cat_artificielle[categorie])

    def sont_categories_compatibles(cat1, cat2):
        ordres1 = ordre_categorie(cat1, typ='check')
        ordres2 = ordre_categorie(cat2, typ='check')
        return any(abs(o1 - o2) <= 1 for o1 in ordres1 for o2 in ordres2)

    def verifier_categorie_existe(row, cat_artificielle):
        categorie = row['Catégorie']
        return categorie in cat_artificielle

    def est_progression_logique(cat1, cat2, cat3, annee_ecart, ecart_annee_1_2, ecart_annee_2_3, score_categ_change):
        ordres = [ordre_categorie(cat, typ='check') for cat in (cat1, cat2, cat3)]
        min_ordres = [min(o) for o in ordres]
        progression_logique_base = False
        #saut logique
        for o1 in ordres[0]:
            for o2 in ordres[1]:
                for o3 in ordres[2]:
                    if (o1 <= o2 <= o3) and ((o3 - o1) >= 0) and ((o3 - o1) <= 5):
                        progression_logique_base = True
                        break
                if progression_logique_base:
                    break
            if progression_logique_base:
                break

            # Si la progression logique de base n'est pas vérifiée, retourner False immédiatement
        if not progression_logique_base:
            return False, score_categ_change

    #saut catégorie junior
        if min_ordres[2] == 3:
            if min_ordres[0] == 1:
                score_categ_change += 2
                return 2 <= annee_ecart <= 4, score_categ_change
            elif min_ordres[1] == 1:
                score_categ_change += 2
                return 2 <= ecart_annee_2_3 <= 4, score_categ_change
            elif min_ordres[1] == 3 and min_ordres[2] == 3:
                score_categ_change += 6
                return 2 <= ecart_annee_1_2 <= 4, score_categ_change
        #saut catégorie espoir
        if min_ordres[2] == 4:
            if min_ordres[1] == 2:
                score_categ_change += 5
                return 3 <= ecart_annee_2_3 <= 5, score_categ_change
            elif min_ordres[0] == 2:
                score_categ_change += 5
                return 3 <= annee_ecart <= 5, score_categ_change
            elif min_ordres[1] == 4 and min_ordres[0] == 1:
                score_categ_change += 5
                return 3 <= ecart_annee_1_2 <= 5, score_categ_change
        #saut catégorie senior
        if min_ordres[2] == 5:
            if min_ordres[1] == 3:
                score_categ_change += 0.5
                return 10 <= ecart_annee_2_3 <= 19, score_categ_change
            elif min_ordres[0] == 3:
                score_categ_change += 0.5
                return 10 <= annee_ecart <= 19, score_categ_change
            elif min_ordres[1] == 4 and min_ordres[0] == 1:
                score_categ_change += 1
                return 10 <= ecart_annee_1_2 <= 19, score_categ_change
        #saut catégorie master
        if min_ordres[2] >= 5 and min_ordres[0] == min_ordres[2] - 2 and min_ordres[0] == min_ordres[1] -1:
            score_categ_change += 3
            return 4 <= annee_ecart <= 21, score_categ_change


        return False, score_categ_change


    def verifier_compatibilite_deux_categories(cat_prec, categorie, annee, annee_prec):
        if sont_categories_compatibles(cat_prec, categorie):
            return True
        return False

    def traiter_categorie(sous_groupe_courant, sous_groupes, row, dict_score_categ_change, score_categ_change, id_sous_groupe):

        annee, categorie = row['Année'], row['Catégorie']
        if len(sous_groupe_courant) < 2:
            sous_groupe_courant.append(row)
            return sous_groupe_courant, sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe

        annee_prec, cat_prec = sous_groupe_courant[-1]['Année'], sous_groupe_courant[-1]['Catégorie']

        if len(sous_groupe_courant) == 2:
            if verifier_compatibilite_deux_categories(cat_prec, categorie, annee, annee_prec):
                sous_groupe_courant.append(row)
                return sous_groupe_courant, sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe
            else:
                sous_groupes.append(pd.DataFrame(sous_groupe_courant))
                dict_score_categ_change[id_sous_groupe] = score_categ_change
                id_sous_groupe = str(uuid.uuid4())
                score_categ_change = 0
                return [row], sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe

        # Pour 3 catégories ou plus
        categories_distinctes = {entry['Catégorie'] for entry in sous_groupe_courant}
        categories_distinctes.add(categorie)
        if len(categories_distinctes) >= 3:
            cat1, cat2, cat3 = sous_groupe_courant[-2]['Catégorie'], sous_groupe_courant[-1]['Catégorie'], categorie
            annee1, annee2, annee3 = sous_groupe_courant[-2]['Année'], sous_groupe_courant[-1]['Année'], annee
            ecart_annee = annee3 - annee1
            ecart_annee_1_2 = annee2 - annee1
            ecart_annee_2_3 = annee3 - annee2
            boole, score_categ_change = est_progression_logique(cat1, cat2, cat3, ecart_annee, ecart_annee_1_2, ecart_annee_2_3,
                                    score_categ_change)
            if boole:
                sous_groupe_courant.append(row)
                return sous_groupe_courant, sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe
            else:
                sous_groupes.append(pd.DataFrame(sous_groupe_courant))
                dict_score_categ_change[id_sous_groupe] = score_categ_change
                id_sous_groupe = str(uuid.uuid4())
                score_categ_change = 0
                return [row], sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe
        else:
            sous_groupe_courant.append(row)
            return sous_groupe_courant, sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe

    def verifier_ordre_croissant(df):
        ordres = df['Ordre'].tolist()
        indices_a_garder = [0]  # Toujours garder le premier élément
        max_ordre = ordres[0]
        for i in range(1, len(ordres)):
            if ordres[i] >= max_ordre:
                indices_a_garder.append(i)
                max_ordre = ordres[i]
        return df.iloc[indices_a_garder]

    def generer_sequences_coherentes(df):
        """
        Génère des séquences cohérentes en réorganisant les lignes du DataFrame.
        Les années peuvent revenir en arrière si l'ordre revient aussi en arrière.

        :param df: DataFrame contenant les colonnes 'Année' et 'Ordre'.
        :return: Liste de DataFrames représentant des séquences cohérentes.
        """
        sorted_df = df.sort_values(by=['Année', 'Ordre']).reset_index(drop=True)

        def construire_sequences(sequence_courante, disponibles):
            if disponibles.empty:
                return [sequence_courante]
            timeout = 500
            sequences = []
            start_time = time.time()
            a=0
            for idx, ligne in disponibles.iterrows():

                nouvelles_disponibles = disponibles.drop(idx)
                nouvelle_sequence = pd.concat([sequence_courante, ligne.to_frame().T], ignore_index=True)
                sequences.extend(construire_sequences(nouvelle_sequence, nouvelles_disponibles))
                a+=1
            return sequences

        return construire_sequences(pd.DataFrame(columns=sorted_df.columns), sorted_df)

    stat_combinaisons_groupes_df = pd.DataFrame(
        columns=['id_combinaison_de_sous_groupes', 'nombres_de_lignes_max_du_dataframe',
                 'nombre_de_ligne_max_du_second_plus_grand_df', 'nombre_de_dataframes'])
    dic_combinaisons = {}
    coureurs_par_categories = exclure_categories_non_existantes(coureurs_par_categories)
    # Créer la colonne 'Ordre'
    df_coureurs = coureurs_par_categories.copy()
    df_coureurs['Ordre'] = coureurs_par_categories['Catégorie'].apply(
        lambda x: ordre_categorie(x, 'ordre') if ordre_categorie(x, 'ordre') is not None else float('inf'))
    opt=False
    # Trier le DataFrame
    trust_optimizer_parts = 0.05
    if len(df_coureurs) <= 5:
        liste_df_coureurs = generer_sequences_coherentes(df_coureurs)
    else:
        opt=True
        liste_df_coureurs = []
        scores = []
        liste_df_coureurs_with_score, trust_optimizer_parts = optimizer.generate_dataframes_list(df_coureurs)
        for df, score in liste_df_coureurs_with_score:
            liste_df_coureurs.append(df)
            scores.append(score)
    if len(liste_df_coureurs) > 120:
        liste_df_coureurs = random.sample(liste_df_coureurs, 120)

    timeout = 500
    start_time = time.time()
    df_index =0
    super_dic_score_categ_change = {}
    if opt:
        dic_score_nomalized = {}
    for df_coureurs in liste_df_coureurs:
        # Créer un ID unique
        id_unique = str(uuid.uuid4())
        if time.time() - start_time > timeout:
            print(f"Temps écoulé pour l'élément passer à l'élément suivant.")
            break  # Sortir de la boucle interne et passer à la prochaine itération
        # Utilisation de la fonction dans la boucle principale
        sous_groupe_courant = []
        sous_groupes = []
        longueur_total = len(df_coureurs)
        dict_score_categ_change = {}
        score_categ_change = 0
        id_sous_groupe = str(uuid.uuid4())
        for _, row in df_coureurs.iterrows():
            sous_groupe_courant, sous_groupes, dict_score_categ_change, score_categ_change, id_sous_groupe = traiter_categorie(sous_groupe_courant, sous_groupes, row, dict_score_categ_change, score_categ_change, id_sous_groupe)

        if sous_groupe_courant:
            for row in sous_groupe_courant:
                sous_groupes.append(pd.DataFrame([row]))
                id_sous_groupe = str(uuid.uuid4())
                dict_score_categ_change[id_sous_groupe] = 0
        super_dic_score_categ_change[id_unique] = dict_score_categ_change
        # Vérifier l'ordre croissant pour chaque sous-groupe
        sous_groupes = [df.sort_values(by='Année').reset_index(drop=True) for df in sous_groupes]
        sous_groupes_verifies = [verifier_ordre_croissant(sg) for sg in sous_groupes]

        # Filtrer les sous-groupes non vides
        groupes_a_fusionner = [sg for sg in sous_groupes_verifies if not sg.empty]

        groupes_a_fusionner = supprimer_ids_communs(groupes_a_fusionner)

        # Calculer les statistiques
        nombre_de_dataframes = len(groupes_a_fusionner)
        if nombre_de_dataframes == 0:
            continue
        tailles = [len(df) for df in groupes_a_fusionner]
        nombres_de_lignes_max_du_dataframe = max(tailles) if tailles else 0
        nombre_de_ligne_max_du_second_plus_grand_df = sorted(tailles, reverse=True)[1] if len(tailles) > 1 else 0

        # Ajouter les statistiques au DataFrame
        stat_combinaisons_groupes_df.loc[len(stat_combinaisons_groupes_df)] = {
            'id_combinaison_de_sous_groupes': id_unique,
            'nombres_de_lignes_max_du_dataframe': nombres_de_lignes_max_du_dataframe,
            'nombre_de_ligne_max_du_second_plus_grand_df': nombre_de_ligne_max_du_second_plus_grand_df,
            'nombre_de_dataframes': nombre_de_dataframes
        }
        if opt:
            dic_score_nomalized[id_unique] = trust_optimizer_parts[df_index]

        # Enregistrer dans le dictionnaire
        dic_combinaisons[id_unique] = groupes_a_fusionner
        df_index+=1
    all_values = [value for sub_dict in super_dic_score_categ_change.values() for value in sub_dict.values()]
    try:
        max_value = max(all_values)
        scaled_super_dic = scale_values(super_dic_score_categ_change, max_value)
    except:
        print('no value')
    stat_combinaisons_groupes_df = stat_combinaisons_groupes_df.sort_values(
        by=['nombres_de_lignes_max_du_dataframe', 'nombre_de_ligne_max_du_second_plus_grand_df',
            'nombre_de_dataframes'],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    try:
        id_meilleur_combi = stat_combinaisons_groupes_df.iloc[0]['id_combinaison_de_sous_groupes']
        groupes_a_fusionner = dic_combinaisons[id_meilleur_combi]
        try:
            best_dic = scaled_super_dic[id_meilleur_combi]
        except:
            best_dic = {}
        if opt:
            optimized_score = dic_score_nomalized[id_meilleur_combi]


        else:
            optimized_score = trust_generative_part
    except:
        return [], 0, {}
    try:
        id_second_meilleur_combi = stat_combinaisons_groupes_df.iloc[1]['id_combinaison_de_sous_groupes']
        groupes_a_fusionner_2 = dic_combinaisons[id_second_meilleur_combi]
    except:
        print('pas de groupes a fusionner 2')

    return groupes_a_fusionner,  optimized_score, best_dic
