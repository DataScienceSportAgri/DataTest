function updateStatistics(stats) {
    // Mise à jour des statistiques de vitesse
    updateStatSection('vitesses', stats.vitesses);
    // Mise à jour des statistiques de distance
    updateStatSection('distances', stats.distances);
}

function updateStatSection(sectionName, sectionStats) {
    const section = document.querySelector(`.stats-section h4:contains('${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)}')`).closest('.stats-section');
    if (section) {
        const table = section.querySelector('table');
        for (const [key, value] of Object.entries(sectionStats)) {
            const row = table.querySelector(`tr:contains('${key}')`);
            if (row) {
                const valueCell = row.querySelector('td:last-child');
                if (valueCell) {
                    valueCell.textContent = formatStatValue(key, value, sectionName);
                }
            }
        }
    }
}

function formatStatValue(key, value, sectionName) {
    const unit = sectionName === 'vitesses' ? 'km/h' : 'm';
    switch (key) {
        case 'moyenne':
        case 'ecart_type':
            return `${value.toFixed(2)} ${unit}`;
        case 'variance':
            return `${value.toFixed(2)} ${unit === 'km/h' ? '(km/h)²' : 'm²'}`;
        case 'pourcentage_variance':
        case 'pourcentage_ecart_type':
            return `${value.toFixed(2)}%`;
        case 'skewness':
        case 'kurtosis':
            return value.toFixed(3);
        default:
            return value.toString();
    }
}