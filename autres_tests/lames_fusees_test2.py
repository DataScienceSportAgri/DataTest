import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
import svgwrite
from scipy.interpolate import interp1d

curve2_x = [0.1,0.2,0.3,0.4,0.5,0.6]
curve3_x = [1,0.9,0.8,0.7,0.6,0.5]
def center_data(x, y):
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)
    return x_centered, y_centered

def close_linestring(x, y):
    if (x[0], y[0]) != (x[-1], y[-1]):
        x = np.append(x, x[0])
        y = np.append(y, y[0])
    return x, y
# Fonction pour générer une courbe lisse avec gestion des segments non croissants
def generate_curve(points):
    x = points[:, 0]
    y = points[:, 1]

    # Vérifier si x est strictement croissant
    if not np.all(x[1:] > x[:-1]):
        # Diviser en segments où x est croissant
        increasing_segments = []
        start_idx = 0
        for i in range(1, len(x)):
            if x[i] <= x[i - 1]:
                increasing_segments.append(points[start_idx:i])
                start_idx = i
        increasing_segments.append(points[start_idx:])

        # Générer des courbes pour chaque segment
        curves_x = []
        curves_y = []
        for segment in increasing_segments:
            segment_x = segment[:, 0]
            segment_y = segment[:, 1]
            if len(segment_x) >= 3:  # Si le segment a au moins trois points
                spline_x = np.linspace(segment_x.min(), segment_x.max(), 100)
                spline_y = make_interp_spline(segment_x, segment_y, k=2)(spline_x)
            else:  # Si le segment a moins de trois points, tracer une ligne droite
                spline_x = segment_x
                spline_y = segment_y
            curves_x.append(spline_x)
            curves_y.append(spline_y)

        return np.concatenate(curves_x), np.concatenate(curves_y)

    # Si x est déjà croissant et contient au moins trois points, interpoler directement
    if len(x) >= 3:
        spline_x = np.linspace(x.min(), x.max(), 200)  # Plus de points pour lisser la courbe
        spline_y = make_interp_spline(x, y, k=3)(spline_x)  # Interpolation cubique
        return spline_x, spline_y

    # Si moins de trois points et croissant, tracer une ligne droite
    return x, y
def normalize_data(x, y):
    x_norm = (x - np.min(x)) / (np.max(x) - np.min(x))
    y_norm = (y - np.min(y)) / (np.max(y) - np.min(y))
    return x_norm, y_norm
def interpolate_curve(x, y, num_points=10000):
    f = interp1d(x, y, kind='linear')
    x_new = np.linspace(min(x), max(x), num_points)
    y_new = f(x_new)
    return x_new, y_new
def plot_and_save_svg(curve2_x, curve3_x, output_file="output.svg"):
    # Courbe supérieure (vallon léger)
    curve1_points = np.array([
        [0, -0.2], [1, -0.3], [2, -0.35], [3, -0.4], [4, -0.42],
        [6, -0.42], [7, -0.4], [8, -0.35], [9, -0.3], [10, -0.2]
    ])

    # Courbe gauche (descendante avec courbure positive)
    curve2_points = np.array([
        [curve2_x[0], 0.1], [curve2_x[1], -0.8], [curve2_x[2], -4.3], [curve2_x[3], -7.1], [curve2_x[4], -9.4],
        [curve2_x[5], -12.7]
    ])

    # Courbe droite (montante avec courbure négative)
    curve3_points = np.array([
        [curve3_x[0], 0.6], [curve3_x[1], -0.75], [curve3_x[2], -2.7], [curve3_x[3], -4.2], [curve3_x[4], -6.5],
        [curve3_x[5], -9.4]
    ])

    def find_closest_intersection_in_zone(curve1_x, curve1_y, curve2_x, curve2_y, x_min, x_max):
        # Filtrer les points dans la zone de recherche
        curve1_x_filtered = [x for x in curve1_x if x_min <= x <= x_max]
        curve1_y_filtered = [curve1_y[i] for i, x in enumerate(curve1_x) if x_min <= x <= x_max]
        curve2_x_filtered = [x for x in curve2_x if x_min <= x <= x_max]
        curve2_y_filtered = [curve2_y[i] for i, x in enumerate(curve2_x) if x_min <= x <= x_max]

        # Trouver l'intersection dans cette zone
        return find_closest_intersection(curve1_x_filtered, curve1_y_filtered, curve2_x_filtered, curve2_y_filtered)

    def find_closest_intersection(curve1_x, curve1_y, curve2_x, curve2_y, tolerance=1e-6):
        # Création des LineStrings
        curve1 = LineString(np.column_stack((curve1_x, curve1_y)))
        curve2 = LineString(np.column_stack((curve2_x, curve2_y)))

        # Buffers pour gérer les erreurs numériques
        buffer_curve1 = curve1.buffer(tolerance)
        buffer_curve2 = curve2.buffer(tolerance)

        # Intersection entre les buffers
        intersections = buffer_curve1.intersection(buffer_curve2)

        if intersections.is_empty:
            print("Aucune intersection trouvée.")
            return None

        print("Type d'intersection détecté :", intersections.geom_type)

        # Gestion des types d'intersections
        if intersections.geom_type == 'Point':
            print("Intersection unique :", (intersections.x, intersections.y))
            return intersections.x, intersections.y
        elif intersections.geom_type == 'MultiPoint':
            print("Intersections multiples :", [p for p in intersections.geoms])
            reference_point = np.array([curve1.coords[0][0], curve1.coords[0][1]])
            closest_point = min(intersections.geoms,
                                key=lambda p: np.linalg.norm(np.array([p.x, p.y]) - reference_point))
            print("Intersection la plus proche :", (closest_point.x, closest_point.y))
            return closest_point.x, closest_point.y
        elif intersections.geom_type == 'Polygon':
            print("Intersection de type Polygon détectée.")
            exterior_coords = list(intersections.exterior.coords)
            if not exterior_coords:
                print("Le Polygon n'a pas de coordonnées extérieures.")
                return None

            print("Coordonnées du Polygon :", exterior_coords)

            # Trouver le sommet le plus proche d'un point de référence
            reference_point = np.array([curve1.coords[0][0], curve1.coords[0][1]])
            closest_point = min(exterior_coords,
                                key=lambda p: np.linalg.norm(np.array(p) - reference_point))
            print("Sommet le plus proche :", closest_point)
            return closest_point[0], closest_point[1]
        elif intersections.geom_type == 'MultiPolygon':
            print("Intersection de type MultiPolygon détectée.")
            reference_point = np.array([curve1.coords[0][0], curve1.coords[0][1]])

            # Trouver le sommet le plus proche dans tous les polygones
            closest_point = None
            min_distance = float('inf')

            for polygon in intersections.geoms:
                exterior_coords = list(polygon.exterior.coords)
                if not exterior_coords:
                    continue
                for p in exterior_coords:
                    distance = np.linalg.norm(np.array(p) - reference_point)
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = p

            if closest_point is not None:
                print("Sommet le plus proche dans MultiPolygon :", closest_point)
                return closest_point[0], closest_point[1]

        else:
            print("Type d'intersection non géré :", intersections.geom_type)

        return None


    # Fonction principale
    def process_curves_and_save(curve1_points, curve2_points, curve3_points):
        # Générer les courbes
        curve1_x, curve1_y = generate_curve(curve1_points)
        curve2_x, curve2_y = generate_curve(curve2_points)
        curve3_x, curve3_y = generate_curve(curve3_points)

        def validate_curve_generation(curve1_points, curve2_points, curve3_points):
            curve1_x, curve1_y = generate_curve(curve1_points)
            curve2_x, curve2_y = generate_curve(curve2_points)
            curve3_x, curve3_y = generate_curve(curve3_points)

            # Afficher les points
            print("Curve 1 (x, y):", list(zip(curve1_x[:5], curve1_y[:5])))  # affichage des 5 premiers points
            print("Curve 2 (x, y):", list(zip(curve2_x[:5], curve2_y[:5])))
            print("Curve 3 (x, y):", list(zip(curve3_x[:5], curve3_y[:5])))

            # Visualiser les courbes
            plt.plot(curve1_x, curve1_y, label="Curve 1")
            plt.plot(curve2_x, curve2_y, label="Curve 2")
            plt.plot(curve3_x, curve3_y, label="Curve 3")
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.title("Validation de la génération des courbes")
            plt.legend()
            plt.grid(True)
            plt.show()

        validate_curve_generation(curve1_points, curve2_points, curve3_points)
        print('curve2_x',curve2_x)
        # Trouver les points de croisement les plus proches

        x1, y1 = find_closest_intersection_in_zone(curve1_x, curve1_y, curve2_x, curve2_y, 0, 1.1)
        x2, y2 = find_closest_intersection_in_zone(curve1_x, curve1_y, curve3_x, curve3_y, 0, 1.1)

        # Créer une droite passant par ces points et étendue de -0.01
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        line_func = lambda x: slope * x + intercept - 0.01

        # Interpoler les courbes
        curve1_x, curve1_y = interpolate_curve(curve1_x, curve1_y)
        curve2_x, curve2_y = interpolate_curve(curve2_x, curve2_y)
        curve3_x, curve3_y = interpolate_curve(curve3_x, curve3_y)

        # Créer des LineString et appliquer un buffer
        line1 = LineString(np.column_stack((curve1_x, curve1_y))).buffer(0.1)
        line2 = LineString(np.column_stack((curve2_x, curve2_y))).buffer(0.1)
        line3 = LineString(np.column_stack((curve3_x, curve3_y))).buffer(0.1)

        # Trouver l'intersection
        intersection_polygon = line1.intersection(line2).intersection(line3)

        if intersection_polygon.is_empty:
            print("Pas d'intersection commune trouvée. Vérifiez les intersections par paires.")

            # Découper la partie sous la droite créée
        minx, miny, maxx, maxy = intersection_polygon.bounds

        # Création des coordonnées des sommets du polygone de découpe
        polygon_coords = [(minx - 10, miny), (maxx + 10, miny),
                          (maxx + 10, line_func(maxx + 10)), (minx - 10, line_func(minx - 10)), (minx - 10, miny)]

        # Vérifier si line_func retourne des valeurs cohérentes
        print("line_func(minx - 10):", line_func(minx - 10))
        print("line_func(maxx + 10):", line_func(maxx + 10))

        # Vérifier les valeurs miny et maxy
        print("miny:", miny)
        print("maxy:", maxy)

        # Fermer le polygone
        polygon_x, polygon_y = zip(*polygon_coords)
        polygon_x, polygon_y = close_linestring(list(polygon_x), list(polygon_y))
        polygon_coords = list(zip(polygon_x, polygon_y))

        # Créer le polygone de découpe
        cutting_polygon = Polygon(polygon_coords)

        # Effectuer la différence
        below_polygon = intersection_polygon.difference(cutting_polygon)

        # Sauvegarder en SVG
        save_to_svg(below_polygon)


    def save_to_svg(polygon):
        dwg = svgwrite.Drawing('output.svg', profile='tiny')

        if polygon.geom_type == 'Polygon':
            coords = list(polygon.exterior.coords)
            dwg.add(dwg.polygon(coords))

        elif polygon.geom_type == 'MultiPolygon':
            for poly in polygon.geoms:
                coords = list(poly.exterior.coords)
                dwg.add(dwg.polygon(coords))

        dwg.save()

    # Appel de la fonction principale avec des données fictives
    process_curves_and_save(curve1_points, curve2_points, curve3_points)

plot_and_save_svg(curve2_x, curve3_x, output_file="output.svg")