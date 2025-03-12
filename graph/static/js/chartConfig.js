function processColorConfig(colors, presets) {
    const colorDict = {};
    const presetMap = new Map();

    // Créer une map des presets pour recherche rapide
    presets.forEach(p => {
        presetMap.set(p.fields.name.toLowerCase(), {
            code: p.fields.color_code,
            id: p.pk
        });
    });

    // Traiter les couleurs
    if (Array.isArray(colors)) {
        colors.forEach(item => {
            if (item.code && item.name) {
                const normalizedName = item.name.toLowerCase();
                const preset = presetMap.get(normalizedName);

                // Structure simplifiée
                colorDict[item.code] = preset ? preset.code : '#808080';
            }
        });
    }

    return {
        dict: colorDict,
        presetMap: Object.fromEntries(presetMap),
        default: '#808080',
        all: presets.map(p => ({
            id: p.pk,
            name: p.fields.name,
            code: p.fields.color_code,
            css: `background-color: ${p.fields.color_code};`
        }))
    };
}

// Fonction de récupération modifiée
function getSafeData(elementId) {
    try {
        const element = document.getElementById(elementId);
        if (!element) return {};
        return JSON.parse(element.textContent);
    } catch (error) {
        console.error(`Erreur chargement ${elementId}:`, error);
        return {};
    }
}

function getValue(id) {
    const element = document.getElementById(id);
    if (!element) return null;

    const value = JSON.parse(element.textContent);
    if (Array.isArray(value)) {
        return value;
    } else if (Number.isInteger(value)) {
        return parseInt(value, 10);
    } else if (typeof value === 'number') {
        return parseFloat(value);
    }
    return value;
}

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




const chartConfig = {
    isUpdate : 'is_update',
    refreshInterval: getValue('refresh_interval'),
    totalCount: getValue('total_count'),
    loadedCount: getValue('loaded_count'),
    minDistance: getValue('min_distance'),
    maxDistance: getValue('max_distance'),
    stats:getValue('stats'),
    categories: getValue('categories'),
    seriesCategories: updateSeriesCategories('series_categories'),
    typeList: getValue('type_list'),
    mode: getValue('mode'),
    colors: processColorConfig(
        getSafeData('colors'),
        getSafeData('colors_presets')
    ).dict,

    preset_colors: processColorConfig(
        getSafeData('colors'),
        getSafeData('colors_presets')
    ).all
};

// Rendre les variables globales si nécessaire
window.chartConfig = chartConfig;
console.log(chartConfig)
// Ici, vous pouvez ajouter le code pour initialiser et configurer votre graphique
// en utilisant les valeurs de chartConfig