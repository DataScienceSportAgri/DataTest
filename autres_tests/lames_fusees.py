import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib.patches import Polygon
# Courbe supérieure (vallon léger)
curve1_points = np.array([
    [0, -0.2], [1, -0.3], [2, -0.35], [3, -0.4], [4, -0.42],
    [6, -0.42], [7, -0.4], [8, -0.35], [9, -0.3], [10, -0.2]
])

# Courbe gauche (descendante avec courbure positive)
curve2_points = np.array([
    [0.1, 0.1], [0.2, -0.8], [0.3, -4.3], [0.4, -7.1], [0.5, -9.4],
    [0.6, -12.7]
])

# Courbe droite (montante avec courbure négative)
curve3_points = np.array([
    [1, 0.6], [0.9, -0.75], [0.8, -2.7], [0.7, -4.2], [0.6, -6.5],
    [0.5, -9.4]
])


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

# Générer les courbes de base
curve1_x, curve1_y = generate_curve(curve1_points)
curve2_x, curve2_y = generate_curve(curve2_points)
curve3_x, curve3_y = generate_curve(curve3_points)

# Tracer les courbes et remplir la surface délimitée par leur intersection
plt.figure(figsize=(8, 8))

# Tracer la courbe supérieure
plt.plot(curve1_x, curve1_y, label="Courbe supérieure", color="red")

# Tracer les courbes gauche et droite ajustées
plt.plot(curve2_x, curve2_y, label="Courbe gauche", color="blue")
plt.plot(curve3_x, curve3_y, label="Courbe droite", color="green")
# Construire le polygone délimitant la surface entre les trois courbes
# Construire le polygone délimitant la surface entre les trois courbes
polygon_points = np.column_stack((
    np.concatenate([curve2_x[::-1], curve1_x, curve3_x]),
    np.concatenate([curve2_y[::-1], curve1_y, curve3_y])
))

# Tracer les courbes et remplir la surface avec un polygone personnalisé
plt.figure(figsize=(8, 8))

# Tracer la courbe supérieure
plt.plot(curve1_x, curve1_y, label="Courbe supérieure", color="red")

# Tracer les courbes gauche et droite
plt.plot(curve2_x, curve2_y, label="Courbe gauche", color="blue")
plt.plot(curve3_x, curve3_y, label="Courbe droite", color="green")

# Ajouter le polygone pour remplir la surface entre les trois courbes
polygon = Polygon(polygon_points, closed=True, facecolor='orange', alpha=0.5)
plt.gca().add_patch(polygon)

# Ajuster l'affichage
plt.title("Intersection des trois courbes formant une surface")
plt.xlabel("X")
plt.ylabel("Y")
plt.grid(True)
plt.legend()
plt.axis('equal')  # Assure des proportions égales sur les axes X et Y
plt.show()