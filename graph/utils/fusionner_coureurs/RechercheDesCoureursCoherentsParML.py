
import pandas as pd
import random
import time
from queue import PriorityQueue
import math

class Optimizer:
    def __init__(self):
        self.catalog = {}
        self.super_patterns = {}

    def record_transitions_with_weights(self, sequence, score):
        # Condition pour retourner si la séquence est supérieure à 7
        if len(sequence) > 7:
            return

        # Création d'une clé de pattern pour la séquence entière
        pattern_key = tuple(
            (item['Catégorie'], item['Ordre'], item['Année'])
            for _, item in sequence.iterrows()
        )

        # Mise à jour du catalogue avec le pattern
        if pattern_key in self.catalog:
            self.catalog[pattern_key]['count'] += 1
            self.catalog[pattern_key]['weight'] += score
        else:
            self.catalog[pattern_key] = {'count': 1, 'weight': score}

        return self.catalog

    def evaluate_sequence(self, sequence):
        score = 0
        previous_year = None
        previous_order = None
        consecutive_drops = 0

        for i in range(1, len(sequence)):
            prev_row = sequence.iloc[i - 1]
            current_row = sequence.iloc[i]

            if (current_row['Année'] < prev_row['Année'] and current_row['Ordre'] < prev_row['Ordre']):
                consecutive_drops += 1
                if consecutive_drops == 1:
                    score += 0.5
                elif consecutive_drops == 2:
                    score = 0
                elif consecutive_drops > 2:
                    score = -1
            elif (current_row['Année'] == prev_row['Année'] and
                  current_row['Ordre'] == previous_order and
                  consecutive_drops >= 2):
                score = -1
            else:
                if (current_row['Année'] > prev_row['Année'] or
                        (current_row['Année'] == prev_row['Année'] and current_row['Ordre'] > prev_row['Ordre'])):
                    score += 0.5
                if (current_row['Année'] > prev_row['Année'] and current_row['Ordre'] == prev_row['Ordre']):
                    score += 1.5
                consecutive_drops = 0

            previous_year = prev_row['Année']
            previous_order = prev_row['Ordre']
            # Ajouter le pattern au catalogue
            self.record_transitions_with_weights(sequence, score)
        return score







    def limit_catalog(self, selected=5000, max_size=20000, keep_between_cleaning=10):
        if len(self.catalog) <= max_size:
            return

        sorted_catalog = sorted(self.catalog.items(), key=lambda x: x[1]['weight'], reverse=True)

        # Sélectionner les meilleurs patterns
        top_patterns = dict(sorted_catalog[:selected])

        # Rechercher de nouveaux super_patterns parmi les meilleurs
        new_super_patterns = {}
        for length in range(2, 8):
            patterns_of_length = [item for item in top_patterns.items() if len(item[0]) == length]
            top_of_length = dict(
                sorted(patterns_of_length, key=lambda x: x[1]['weight'], reverse=True)[:keep_between_cleaning])
            new_super_patterns.update(top_of_length)

        # Mettre à jour les super_patterns
        self.super_patterns.update(new_super_patterns)

        # Combiner les super_patterns avec les meilleurs patterns
        final_catalog = {**self.super_patterns, **top_patterns}

        # S'assurer que la taille finale ne dépasse pas max_size
        if len(final_catalog) > max_size:
            sorted_final = sorted(final_catalog.items(), key=lambda x: x[1]['weight'], reverse=True)
            final_catalog = dict(sorted_final[:max_size])

        # Mettre à jour le catalog et les super_patterns
        self.catalog = {k: v for k, v in final_catalog.items() if k not in self.super_patterns}
        self.super_patterns = {k: v for k, v in final_catalog.items() if k in self.super_patterns}

    def get_all_patterns(self):
        all_patterns = {**self.catalog, **self.super_patterns}

        # 10 patterns avec le plus haut score
        top_10_patterns = sorted(all_patterns.items(), key=lambda x: x[1]['weight'], reverse=True)[:10]

        # Score moyen par longueur
        length_scores = {length: [] for length in range(2, 8)}
        for pattern, data in all_patterns.items():
            length = len(pattern)
            if 2 <= length <= 7:
                length_scores[length].append(data['weight'])

        average_scores = {
            length: (sum(scores) / len(scores) if scores else 0)
            for length, scores in length_scores.items()
        }

        # Nombre de patterns par longueur
        pattern_counts = {length: 0 for length in range(2, 8)}
        for pattern in all_patterns.keys():
            length = len(pattern)
            if 2 <= length <= 7:
                pattern_counts[length] += 1

        # Pattern le plus enregistré
        most_recorded_pattern = max(all_patterns.items(), key=lambda x: x[1]['count'])

        return {
            'top_10_patterns': dict(top_10_patterns),
            'average_scores': average_scores,
            'pattern_counts': pattern_counts,
            'most_recorded_pattern': most_recorded_pattern
        }




    def process_dataframe(self, df):
        def fraction_dataframe(df):
            available_indices = list(df.index)
            random.shuffle(available_indices)
            sequences = []
            while available_indices:
                if len(available_indices) < 2:
                    seq_length = len(available_indices)
                else:
                    seq_length = random.randint(2, min(7, len(available_indices)))
                seq_indices = available_indices[:seq_length]
                sequence = df.loc[seq_indices]
                sequences.append(sequence)
                available_indices = available_indices[seq_length:]
            return sequences

        def generate_sequences(self, sequence):
            result = pd.DataFrame(columns=sequence.columns)
            available_indices = set(sequence.index)
            while available_indices:
                window_size = min(7, len(result) + 1)
                if len(result) < 2:
                    idx = random.choice(list(available_indices))
                else:
                    window = result.iloc[-window_size:]
                    candidates = []
                    for idx in available_indices:
                        potential_window = pd.concat([window, sequence.loc[[idx]]])
                        pattern_key = tuple(
                            (row['Catégorie'], row['Ordre'], row['Année']) for _, row in potential_window.iterrows())
                        if pattern_key in self.catalog:
                            candidates.append((idx, self.catalog[pattern_key]['weight']))
                    if candidates and random.random() < 0.8:
                        idx = max(candidates, key=lambda x: x[1])[0]
                    else:
                        idx = random.choice(list(available_indices))

                result = pd.concat([result, sequence.loc[[idx]]])
                available_indices.remove(idx)
                self.evaluate_sequence(result)
            return result.reset_index(drop=True)



        fractioned_sequences = fraction_dataframe(df)
        generated_sequences = []

        # Générer des séquences jusqu'à ce que nous ayons suffisamment de lignes
        while sum(len(seq) for seq in generated_sequences) < len(df):
            sequence = random.choice(fractioned_sequences)
            generated_sequence = generate_sequences(self, sequence)
            generated_sequences.append(generated_sequence)

        # Concaténer toutes les séquences générées
        final_dataframe = pd.concat(generated_sequences)

        # Tronquer ou compléter pour avoir exactement le même nombre de lignes que l'entrée
        if len(final_dataframe) > len(df):
            final_dataframe = final_dataframe.iloc[:len(df)]
        elif len(final_dataframe) < len(df):
            remaining_rows = df.iloc[len(final_dataframe):].sample(frac=1)  # Mélanger les lignes restantes
            final_dataframe = pd.concat([final_dataframe, remaining_rows])

        return final_dataframe.reset_index(drop=True)

    def remove_duplicates(self, dataframes):
        unique_dataframes = []
        seen_dataframes = set()
        for df in dataframes:
            # Créer une représentation hashable du dataframe
            df_hash = tuple(tuple(row) for row in df.itertuples(index=False, name=None))
            if df_hash not in seen_dataframes:
                seen_dataframes.add(df_hash)
                unique_dataframes.append(df)
        return unique_dataframes

    def generate_dataframes_list(self, dataframe, itteration_max=300, selection_parmi=200, nb_list=120):
        # Génération de itteration_max dataframes
        self.limit_catalog(
            selected=3000,max_size=8000, keep_between_cleaning=10)
        dataframes = []
        for _ in range(itteration_max):
            df_generated = self.process_dataframe(dataframe)
            dataframes.append(df_generated)

        dataframes_unique = self.remove_duplicates(dataframes)
        # Calcul du score pour chaque dataframe unique
        dataframes_with_scores = []
        min_score = float(0)
        max_score = float(1)

        for df in dataframes_unique:
            score = self.evaluate_sequence(df)
            dataframes_with_scores.append((df, score))
            min_score = min(min_score, score)
            max_score = max(max_score, score)
            # Sélection des meilleurs dataframes
        trust_optimizer_parts = []
        for df, score in dataframes_with_scores:
            if max_score != min_score:
                normalized_score = 0.05 * (score - min_score) / (max_score - min_score)
            else:
                normalized_score = 0.025 # Si tous les scores sont identiques, on assigne 0.025
            trust_optimizer_parts.append(normalized_score)
        dataframes_with_scores_sorted = sorted(dataframes_with_scores, key=lambda x: x[1], reverse=True)
        top_dataframes = dataframes_with_scores_sorted[:selection_parmi]

        # Sélection aléatoire parmi les meilleurs dataframes
        selected_dataframes = random.sample(top_dataframes, min(nb_list, len(top_dataframes)))

        return selected_dataframes, trust_optimizer_parts