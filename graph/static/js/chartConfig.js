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
};

// Rendre les variables globales si nécessaire
window.chartConfig = chartConfig;

// Exemple d'utilisation
console.log('Configuration du graphique:', chartConfig);
console.log('Configuration du graphique avec window:', window.chartConfig);
// Ici, vous pouvez ajouter le code pour initialiser et configurer votre graphique
// en utilisant les valeurs de chartConfig