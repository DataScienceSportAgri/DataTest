function generateStatsDivs(stats) {
    const container = document.getElementById('dynamic-stats-container');
    if (!container) {
        console.error("Container element not found");
        return;
    }
    container.innerHTML = ''; // Vider le conteneur

    // Créer la division pour les distances
    const distancesDiv = document.createElement('div');
    distancesDiv.className = 'distances-container';
    distancesDiv.innerHTML = '<h4>Distances</h4>';

    // Convertir la chaîne HTML en élément DOM
    const tableHtml = generateStatsTable(stats.distances, 'distances');
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = tableHtml;
    distancesDiv.appendChild(tempDiv.firstElementChild);

    container.appendChild(distancesDiv);

    const vitessesDiv = document.createElement('div');
    vitessesDiv.className = 'vitesses-container';

    // Ajouter le titre h4
    const titleH4 = document.createElement('h4');
    titleH4.textContent = 'Vitesses';
    vitessesDiv.appendChild(titleH4);

    // Créer un conteneur pour la grille des séries
    const vitessesGrid = document.createElement('div');
    vitessesGrid.className = 'vitesses-grid';

    // Ajouter une classe dynamique basée sur le nombre de séries
    const seriesCount = Object.keys(stats.vitesses).length;
    vitessesGrid.classList.add(`vitesses-grid-${seriesCount}`);

    // Générer les divisions pour chaque série de vitesses
    Object.entries(stats.vitesses).forEach(([serieName, serieStats]) => {
        const serieDiv = document.createElement('div');
        serieDiv.className = 'stats-flex-container';

        // Convertir la chaîne HTML en élément DOM
        const serieTableHtml = generateStatsTable(serieStats, 'vitesses');
        serieDiv.innerHTML = `
            <div class="stats-section">
                <h5>${serieName}</h5>
            </div>
        `;
        const tempSerieDiv = document.createElement('div');
        tempSerieDiv.innerHTML = serieTableHtml;
        serieDiv.querySelector('.stats-section').appendChild(tempSerieDiv.firstElementChild);

        vitessesGrid.appendChild(serieDiv);  // Ajouter serieDiv à vitessesGrid
    });

    vitessesDiv.appendChild(vitessesGrid);  // Ajouter vitessesGrid à vitessesDiv
    container.appendChild(vitessesDiv);
}




function generateStatsTable(statData, type) {
    if (!statData) return '<p>Aucune donnée disponible</p>';

    const rows = [];
    const units = {
        'distances': {
            'default': 'km',
            'n': ' ',
            'skewness': ' '
        },
        'vitesses': {
            'default': 'km/h',
            'variance': '(km/h)²',
            'n': ' ',
            'pourcentage_variance': '%',
            'pourcentage_ecart_type': '%',
            'pourcentage_ecart_type_droit': '%',
            'pourcentage_ecart_type_gauche': '%',
            'skewness': ' ',
            'kurtosis': ' '
        }
    };

    Object.entries(statData).forEach(([key, value]) => {
        let formattedValue = value;
        let unit = units[type][key] || units[type]['default'] || '';

        // Formatage spécifique pour certaines clés
        if (typeof value === 'number') {
            if (['n', 'skewness'].includes(key)) {
                formattedValue = value.toFixed(0);
            } else if (key.startsWith('pourcentage')) {
                formattedValue = value.toFixed(2);
            } else {
                formattedValue = value.toFixed(2);
            }
        }

        // Formatage du nom de la clé pour l'affichage
        const displayKey = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');

        rows.push(`<tr><td>${displayKey} :</td><td>${formattedValue}${unit ? ' ' + unit : ''}</td></tr>`);
    });

    return `<table>${rows.join('')}</table>`;
}

// Appelez la fonction generateStatsDivs avec l'objet stats
generateStatsDivs(window.chartConfig.stats);


