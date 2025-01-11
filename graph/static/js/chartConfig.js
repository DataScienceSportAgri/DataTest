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



const chartConfig = {
    isUpdate : 'is_update',
    refreshInterval: getValue('refresh_interval'),
    totalCount: getValue('total_count'),
    loadedCount: getValue('loaded_count'),
    minDistance: getValue('min_distance'),
    maxDistance: getValue('max_distance'),
    categories: getValue('categories'),
    seriesCategories: getValue('series_categories'),
    typeList: getValue('type_list')
};

// Rendre les variables globales si nécessaire
window.chartConfig = chartConfig;

// Exemple d'utilisation
console.log('Configuration du graphique:', chartConfig);

// Ici, vous pouvez ajouter le code pour initialiser et configurer votre graphique
// en utilisant les valeurs de chartConfig