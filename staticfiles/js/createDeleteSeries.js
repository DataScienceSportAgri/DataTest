// UpdateColors.js
class ColorUpdater {
    constructor() {
        this.defaultColors = new Map();
        this.initializeDefaults();
        this.initializeEventListeners();
    }

    // Initialise les couleurs par défaut depuis chartConfig
    initializeDefaults() {
        try {
            if (window.chartConfig?.colors) {
                this.defaultColors = new Map(
                    Object.entries(window.chartConfig.colors.dict || {})
                );
            }
        } catch (error) {
            console.error('Erreur initialisation des couleurs:', error);
        }
    }

    // Gestionnaire d'événements pour les sélecteurs de couleur
    initializeEventListeners() {
        document.querySelectorAll('.color-group select').forEach(select => {
            select.addEventListener('change', this.handleColorChange.bind(this));
        });
    }

    // Met à jour chartConfig lors d'un changement de couleur
handleColorChange(event) {
    const select = event.target;
    const seriesContainer = select.closest('.category-container');
    const titleInput = seriesContainer?.querySelector('.titre-serie');

    if (!titleInput) {
        console.error('Élément titre introuvable');
        return;
    }

    const seriesName = titleInput.value.trim();
    const newColor = select.value;
    const presetId = select.options[select.selectedIndex].dataset.presetId;

    // Mise à jour de la configuration globale
    this.updateChartConfig(seriesName, newColor, presetId);
    this.updateColorPreview(select.nextElementSibling, newColor);

    // Log des couleurs après chaque changement
    console.log('Couleurs mises à jour:', JSON.parse(JSON.stringify(window.chartConfig.colors)));
}

    // Met à jour window.chartConfig avec la nouvelle couleur
    updateChartConfig(seriesName, colorCode) {
            // Accès direct à colors sans passer par .dict
            window.chartConfig.colors[seriesName] = {
            code: colorCode,
            preset_id: this.findPresetId(colorCode),
            };
    }


    // Récupère le nom d'une couleur par son ID
    getColorName(presetId) {
        return window.chartConfig.preset_colors.find(p => p.id === presetId)?.name;
    }

        // Ajouter cette méthode à votre classe ColorUpdater
    findPresetId(colorCode) {
        return window.chartConfig.preset_colors.find(p => p.code === colorCode)?.id || null;
    }

    // Met à jour l'aperçu visuel
    updateColorPreview(previewElement, colorCode) {
        if (previewElement) {
            previewElement.style.backgroundColor = colorCode;
        }
    }

getUnusedPresetColor() {
    // Extraire directement les codes couleur
    const usedColors = new Set(
        Object.values(window.chartConfig.colors).map(color =>
            typeof color === 'object' && color.code && typeof color.code === 'object'
                ? color.code.code  // Structure imbriquée
                : typeof color === 'object'
                    ? color.code   // Structure simple objet
                    : color        // Chaîne directe
        )
    );

    // Filtrer les presets disponibles
    const availablePresets = window.chartConfig.preset_colors.filter(
        p => !usedColors.has(p.code)
    );

    return availablePresets.length > 0
        ? availablePresets[Math.floor(Math.random() * availablePresets.length)].code
        : window.chartConfig.preset_colors[0]?.code || '#808080';
}

    createColorPicker(seriesName, defaultColor) {
    // Normalisation de la couleur
    const normalizedColor = typeof defaultColor === 'object'
        ? (defaultColor.code?.code || defaultColor.code || '#808080')
        : defaultColor;

    console.log(`Création du picker pour ${seriesName} avec couleur:`, normalizedColor);
        // Création du groupe de sélection
        const colorGroup = document.createElement('div');
        colorGroup.className = 'color-group';
        colorGroup.style.marginLeft = '20px';

        const colorLabel = document.createElement('label');
        colorLabel.textContent = 'Couleur : ';

        // Création du select
        const colorSelect = document.createElement('select');
        colorSelect.className = 'color-preset-select';
        colorSelect.dataset.seriesName = seriesName;

        // Peuplement des options
        window.chartConfig.preset_colors.forEach(preset => {
            const option = document.createElement('option');
            option.value = preset.code;
            option.textContent = preset.name;
            option.dataset.presetId = preset.id;
            option.style = preset.css + 'padding: 3px; border-radius: 3px;';

            // Sélectionner l'option correspondant à la couleur par défaut
        if (preset.code === normalizedColor) {
            option.selected = true;
        }

            colorSelect.appendChild(option);
        });

        // Prévisualisation de la couleur
        const colorPreview = document.createElement('span');
        colorPreview.className = 'color-preview';
        colorPreview.style.display = 'inline-block';
        colorPreview.style.width = '20px';
        colorPreview.style.height = '20px';
        colorPreview.style.marginLeft = '10px';
        colorPreview.style.border = '1px solid #000';
        colorPreview.style.backgroundColor = defaultColor;

        // Gestion du changement de couleur
        colorSelect.addEventListener('change', this.handleColorChange.bind(this));

        // Assemblage des éléments
        colorLabel.appendChild(colorSelect);
        colorLabel.appendChild(colorPreview);
        colorGroup.appendChild(colorLabel);

        return colorGroup;
    }
}



document.addEventListener('DOMContentLoaded', function() {
    colorUpdater = new ColorUpdater();
    const addButton = document.querySelector('#bouton\\+');
    const removeButton = document.querySelector('#bouton\\-');
    const container = document.querySelector('#series_container');
    let seriesCount = 0;

    const rawData = document.getElementById('categories').textContent;
    const categoriesData = JSON.parse(JSON.parse(rawData));

    container.style.display = 'flex';
    container.style.flexDirection = 'row';
    container.style.flexWrap = 'wrap';
    container.style.gap = '10px';

    createInitialSeries();

function updateSeriesCategories() {
    const seriesCategories = {};
    const seriesDivs = document.querySelectorAll('#series_container > div');

    seriesDivs.forEach(seriesDiv => {
        const seriesName = seriesDiv.querySelector('.titre-serie').value;
        const categoryBoxes = seriesDiv.querySelectorAll('.category-box');
        const categories = {
            sexe: [],
            nom: []
        };

        categoryBoxes.forEach(box => {
            categories.nom.push(box.textContent);
            if (!categories.sexe.includes(box.dataset.sexe)) {
                categories.sexe.push(box.dataset.sexe);
            }
        });

        seriesCategories[seriesName] = categories;
    });

    return seriesCategories;
}
// Gestionnaire pour le changement de nom des séries
function setupTitleChangeListeners() {
    document.addEventListener('change', function(e) {
        // Vérifier si c'est un champ de titre de série qui a été modifié
        if (e.target.classList.contains('titre-serie')) {
            const oldName = e.target.defaultValue;
            const newName = e.target.value.trim();

            // Ne rien faire si le nom n'a pas changé
            if (oldName === newName) return;

            console.log(`Série renommée: ${oldName} → ${newName}`);

            // Récupérer la couleur associée à l'ancien nom
            if (window.chartConfig.colors[oldName]) {
                // Copier la couleur vers le nouveau nom
                window.chartConfig.colors[newName] = window.chartConfig.colors[oldName];

                // Supprimer l'ancienne entrée
                delete window.chartConfig.colors[oldName];

                // Mettre à jour les catégories
                window.chartConfig.seriesCategories = updateSeriesCategories();

                console.log('Couleurs mises à jour:', window.chartConfig.colors);
            }

            // Mettre à jour la valeur par défaut pour les futurs changements
            e.target.defaultValue = newName;
        }
    });
}


function createInitialSeries() {
    // Récupérer les couleurs depuis chartConfig
    const colors = window.chartConfig.colors || {};

    // Créer la série F avec sa couleur associée
    const fColor = colors['F'] || null; // Sera null si la couleur n'existe pas
    createSeriesWithTitle('F', fColor);

    // Créer la série M avec sa couleur associée
    const mColor = colors['M'] || null;
    createSeriesWithTitle('M', mColor);

    // Mettre à jour les catégories de séries
    window.chartConfig.seriesCategories = updateSeriesCategories();
}

    function dragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.textContent);
    }

function createSeriesWithTitle(title, color) {
    seriesCount++;
    const newSeriesDiv = document.createElement('div');

    // Récupération de la couleur automatique si non fournie
    const autoColor = color || colorUpdater.getUnusedPresetColor();
    // Récupération directe depuis l'objet global
        // Mise à jour de la configuration globale
    colorUpdater.updateChartConfig(title, autoColor);



    newSeriesDiv.className = 'category-container';
    newSeriesDiv.id = `categorie_selected_uniques_series_${seriesCount}`;

        // Ajoutez ces styles
    newSeriesDiv.style.width = '550px'; // Ajustez selon vos besoins
    newSeriesDiv.style.flexShrink = '0';
    newSeriesDiv.style.marginBottom = '10px';

    // Conteneur pour le titre éditable et le bouton de suppression
    const headerContainer = document.createElement('div');
    headerContainer.style.display = 'flex';
    headerContainer.style.justifyContent = 'space-between';
    headerContainer.style.alignItems = 'center';
    headerContainer.style.marginBottom = '10px';
    // Positionnement du titre en haut à gauche avec une marge
    headerContainer.style.position = 'relative'; // Permet d'utiliser top et left
    headerContainer.style.top = '5px'; // 5px depuis le haut
    headerContainer.style.left = '5px'; // 5px depuis la gauche

    // Champ d'édition du titre
    const seriesTitleInput = document.createElement('input');
    seriesTitleInput.type = 'text';
    seriesTitleInput.value = title || `Série ${seriesCount}`;
    seriesTitleInput.defaultValue = title || `Série ${seriesCount}`;
    // Ajout d'une classe commune
    seriesTitleInput.classList.add('titre-serie');

    // Styles pour ressembler à un <h4>
    seriesTitleInput.style.fontSize = '1.5em'; // Taille similaire à <h4>
    seriesTitleInput.style.fontWeight = 'bold'; // Gras comme un titre
    seriesTitleInput.style.border = 'none'; // Pas de bordure pour ressembler à un texte
    seriesTitleInput.style.outline = 'none'; // Pas de contour lors du focus
    seriesTitleInput.style.backgroundColor = 'transparent'; // Fond transparent
    seriesTitleInput.style.width = '100%'; // Occupe toute la largeur disponible
    seriesTitleInput.style.marginRight = '10px'; // Ajustement de l'espacement
    seriesTitleInput.style.padding = '0'; // Pas de padding pour ressembler à un texte brut

        // Bouton pour supprimer la série
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Supprimer';
    deleteButton.style.backgroundColor = '#ff4d4d'; // Couleur rouge pour indiquer une action destructive
    deleteButton.style.color = '#fff';
    deleteButton.style.border = 'none';
    deleteButton.style.padding = '5px 10px';
    deleteButton.style.cursor = 'pointer';
    // Création du groupe de sélection de couleur avec la méthode de ColorUpdater
    const colorGroup = colorUpdater.createColorPicker(title, autoColor);

    // Ajout des éléments au conteneur d'en-tête
    headerContainer.appendChild(seriesTitleInput);
    headerContainer.appendChild(colorGroup);
    headerContainer.appendChild(deleteButton);
    newSeriesDiv.appendChild(headerContainer);
        // Ajout des éléments au conteneur d'en-tête



    // Ajouter les catégories correspondantes
    for (const category of categoriesData) {
        if (category.sexe === title) {
            const box = document.createElement('div');
            box.className = 'category-box';
            box.draggable = true;
            box.textContent = category.nom;
            box.dataset.sexe = category.sexe;
            newSeriesDiv.appendChild(box);

            box.addEventListener('dragstart', dragStart);
        }
    }

    container.appendChild(newSeriesDiv);

    // Gestion du bouton de suppression
    deleteButton.addEventListener('click', function () {
        // Renvoyer les éléments "draggable" dans la boîte all-categories
        const draggableElements = newSeriesDiv.querySelectorAll('.category-box');
        draggableElements.forEach(box => {
            allCategorieDiv.appendChild(box);
        });

        // Supprimer la série
        container.removeChild(newSeriesDiv);
        });
     return newSeriesDiv;
}
function removeLastSeries() {
    if (seriesCount > 2) {  // Ne supprime pas les séries F et M
        const lastSeries = document.querySelector(`#categorie_selected_uniques_series_${seriesCount}`);

        if (lastSeries) {
            // Récupérer le nom de la série
            const seriesName = lastSeries.querySelector('.titre-serie').value;

            // Déplacer les éléments draggable vers la zone all-categories
            const draggableElements = lastSeries.querySelectorAll('.category-box');
            draggableElements.forEach(box => {
                if (allCategorieDiv) {  // Vérifier que allCategorieDiv existe
                    allCategorieDiv.appendChild(box);
                }
            });

            // Supprimer la référence couleur (gestion des deux formats possibles)
            if (window.chartConfig.colors) {
                if (window.chartConfig.colors.dict) {
                    delete window.chartConfig.colors.dict[seriesName];
                } else {
                    delete window.chartConfig.colors[seriesName];
                }
            }

            // Supprimer la série du DOM
            lastSeries.remove();
            seriesCount--;

            // Retourner le nom de la série supprimée (utile pour le débogage)
            return seriesName;
        }
    }
    return null; // Aucune série supprimée
}



addButton.addEventListener('click', () => {
   createSeriesWithTitle();

    // Mettre à jour les catégories
    window.chartConfig.seriesCategories = updateSeriesCategories();
});

// Gestionnaire d'événements simplifié
removeButton.addEventListener('click', () => {
    const removedSeries = removeLastSeries();

    if (removedSeries) {
        // Mettre à jour les catégories
        window.chartConfig.seriesCategories = updateSeriesCategories();
        console.log(`Série supprimée: ${removedSeries}`);
    }
});
setupTitleChangeListeners();
});
