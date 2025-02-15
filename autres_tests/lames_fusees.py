import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib.patches import Polygon
import matplotlib.path as mpath
from matplotlib.patches import PathPatch


curve2_x = [0.1,0.2,0.3,0.4,0.5,0.6]
curve3_x = [1,0.9,0.8,0.7,0.6,0.5]
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
    # Créer la figure et l'axe
    fig, ax = plt.subplots(figsize=(8, 8))

    # Tracer les courbes
    ax.plot(curve1_x, curve1_y, label="Courbe supérieure", color="red")
    ax.plot(curve2_x, curve2_y, label="Courbe gauche", color="blue")
    ax.plot(curve3_x, curve3_y, label="Courbe droite", color="green")

    # Créer le polygone
    polygon_points = np.vstack((
        np.column_stack((curve2_x[::-1], curve2_y[::-1])),
        np.column_stack((curve1_x, curve1_y)),
        np.column_stack((curve3_x, curve3_y))
    ))

    polygon = Polygon(polygon_points, closed=True, facecolor='orange', alpha=0.5)
    ax.add_patch(polygon)

    # Configurer les limites du graphique
    ax.set_xlim(min(curve2_x[0], curve3_x[-1]), max(curve2_x[-1], curve3_x[0]))
    ax.set_ylim(min(min(curve2_y), min(curve3_y)), max(curve1_y))

    # Créer un masque pour cacher tout ce qui est en dehors du polygone
    path = mpath.Path(polygon_points)
    patch = PathPatch(path, facecolor='none')
    ax.add_patch(patch)
    ax.set_clip_path(patch)

    # Configurer l'apparence
    ax.set_title("Surface entre les trois courbes")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)
    ax.legend()
    ax.axis('equal')

    # Sauvegarder en SVG
    plt.savefig(output_file, format='svg', bbox_inches='tight')
    plt.close(fig)

plot_and_save_svg(curve2_x, curve3_x, "output.svg")