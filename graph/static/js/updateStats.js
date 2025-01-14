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
    console.log('Updating distance stats:', distanceStats);
    console.log('Distance keys:', keys);

    const $container = $('.distances-container');
    console.log('Distance container found:', $container.length);

    if ($container.length) {
        const $table = $container.find('table');
        console.log('Distance table found:', $table.length);

        if ($table.length) {
            keys.forEach(key => {
                console.log(`Updating distance stat: ${key}`);
                const $row = $table.find(`tr:has(td:first-child:contains("${key}"))`);
                console.log(`Row for ${key} found:`, $row.length);

                if ($row.length) {
                    const $valueCell = $row.find('td:last-child');
                    console.log(`Value cell for ${key} found:`, $valueCell.length);

                    if ($valueCell.length) {
                        const newValue = formatStatValue(key, distanceStats[key], 'distances');
                        console.log(`Updating ${key} with value:`, newValue);
                        $valueCell.text(newValue);
                    }
                }
            });
        }
    }
}

function updateVitesseStats(vitesseStats, keys, series) {
    console.log('Updating vitesse stats:', vitesseStats);
    console.log('Vitesse keys:', keys);
    console.log('Vitesse series:', series);

    const $container = $('.vitesses-container');
    console.log('Vitesse container found:', $container.length);

    if ($container.length) {
        series.forEach(serieName => {
            console.log(`Updating serie: ${serieName}`);
            const serieStats = vitesseStats[serieName];
            const $serieSection = $container.find(`.stats-flex-container:has(h5:contains("${serieName}"))`);
            console.log(`Serie section for ${serieName} found:`, $serieSection.length);

            if ($serieSection.length) {
                const $table = $serieSection.find('table');
                console.log(`Table for ${serieName} found:`, $table.length);

                if ($table.length) {
                    keys.forEach(key => {
                        console.log(`Updating stat ${key} for serie ${serieName}`);
                        const $row = $table.find(`tr:has(td:first-child:contains("${key}"))`);
                        console.log(`Row for ${key} in ${serieName} found:`, $row.length);

                        if ($row.length) {
                            const $valueCell = $row.find('td:last-child');
                            console.log(`Value cell for ${key} in ${serieName} found:`, $valueCell.length);

                            if ($valueCell.length) {
                                const newValue = formatStatValue(key, serieStats[key], 'vitesses');
                                console.log(`Updating ${key} in ${serieName} with value:`, newValue);
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
        case 'ecart_type':
        case 'mediane':
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

const result = extractKeys(window.chartConfig.stats);
console.log(result);

