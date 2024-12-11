function getValue(id) {
    const value = JSON.parse(document.getElementById(id).textContent);
    if (Number.isInteger(value)) {
        return getIntValue(id);
    } else {
        return parseFloat(value);
    }
}
function getIntValue(id) {
    return parseInt(JSON.parse(document.getElementById(id).textContent), 10);
}



const chartConfig = {
    isUpdate : 'is_update',
    refreshInterval: getValue('refresh_interval'),
    totalCount: getValue('total_count'),
    loadedCount: getValue('loaded_count'),
    minDistance: getValue('min_distance'),
    maxDistance: getValue('max_distance')
};

// Rendre les variables globales si nécessaire
window.chartConfig = chartConfig;

// Exemple d'utilisation
console.log('Configuration du graphique:', chartConfig);

// Ici, vous pouvez ajouter le code pour initialiser et configurer votre graphique
// en utilisant les valeurs de chartConfig