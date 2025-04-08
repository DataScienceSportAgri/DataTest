function updateStatistics(stats) {
    const { distanceKeys, vitesseKeys, vitesseSeries } = extractKeys(stats);

    // Mise à jour des statistiques de distance
    updateDistanceStats(stats.distances, distanceKeys);

    // Mise à jour des statistiques de vitesse
    updateVitesseStats(stats.vitesses, vitesseKeys, vitesseSeries);
}

function extractKeys(stats) {
    const distanceKeys = Object.keys(stats.distances || {});
    const vitesseSeries = Object.keys(stats.vitesses || {});
    const vitesseKeys = vitesseSeries.length > 0 ? Object.keys(stats.vitesses[vitesseSeries[0]] || {}) : [];
    return { distanceKeys, vitesseKeys, vitesseSeries };
}

function updateDistanceStats(distanceStats, keys) {


    const $container = $('.distances-container');

    if ($container.length) {
        const $table = $container.find('table');

        if ($table.length) {
            keys.forEach(key => {
                const $row = $table.find(`tr[data-key="${key}"]`);

                if ($row.length) {
                    const $valueCell = $row.find('td:last-child');

                    if ($valueCell.length) {
                        const newValue = formatStatValue(key, distanceStats[key], 'distances');
                        $valueCell.text(newValue);
                    }
                }
            });
        }
    }
}

function updateVitesseStats(vitesseStats, keys, series) {

    const $container = $('.vitesses-container');

    if ($container.length) {
        series.forEach(serieName => {
            const serieStats = vitesseStats[serieName];
            const $serieSection = $container.find(`.stats-flex-container:has(h5:contains("${serieName}"))`);

            if ($serieSection.length) {
                const $table = $serieSection.find('table');

                if ($table.length) {
                    keys.forEach(key => {
                        const $row = $table.find(`tr[data-key="${key}"]`);

                        if ($row.length) {
                            const $valueCell = $row.find('td:last-child');

                            if ($valueCell.length) {
                                const newValue = formatStatValue(key, serieStats[key], 'vitesses');
                                $valueCell.text(newValue);
                            }
                        }
                    });
                }
            }
        });
    }
}


function formatStatValue(key, value, sectionName) {
    const unit = sectionName === 'vitesses' ? 'km/h' : 'm';
    switch (key) {
        case 'moyenne':
            return value.toFixed(3);
        case 'ecart type':
            return value.toFixed(3);
        case 'mediane':
            return `${value.toFixed(2)} ${unit}`;
        case 'variance':
            return `${value.toFixed(2)} ${unit === 'km/h' ? '(km/h)²' : 'm²'}`;
        case 'pourcentage variance':
            return `${value.toFixed(2)}%`;
        case 'pourcentage ecart type droit':
            return `${value.toFixed(2)}%`;
        case 'pourcentage ecart type gauche':
            return `${value.toFixed(2)}%`;
        case 'skewness':
            return value.toFixed(3);
        case 'kurtosis':
            return value.toFixed(3);
        default:
            return value.toString();
    }
}

const result = extractKeys(window.chartConfig.stats);
console.log(result);

