document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.querySelector('#bouton\\+');
    const removeButton = document.querySelector('#bouton\\-');
    const container = document.querySelector('#categorie_selected');
    let seriesCount = 0;

    const rawData = document.getElementById('categories').textContent;
    const categoriesData = JSON.parse(JSON.parse(rawData));

    // Style pour le conteneur principal
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '10px';

    // Créer les trois divisions initiales
    createInitialSeries();

    function createInitialSeries() {

        createSeriesWithTitle('F');
        // Série pour hommes
        createSeriesWithTitle('M');
    }

    function createSeriesWithTitle(title) {
        const newSeriesDiv = document.createElement('div');
        newSeriesDiv.className = 'category-container';
        newSeriesDiv.id = `categorie_selected_${title}`;

        newSeriesDiv.style.width = '100%';
        newSeriesDiv.style.padding = '10px';
        newSeriesDiv.style.backgroundColor = '#f0f0f0';
        newSeriesDiv.style.borderRadius = '5px';
        newSeriesDiv.style.marginBottom = '10px';

        const seriesTitle = document.createElement('h4');
        seriesTitle.textContent = title;
        newSeriesDiv.appendChild(seriesTitle);

        container.appendChild(newSeriesDiv);
    }


    // Fonction pour supprimer la dernière série
    function removeLastSeries() {
        if (seriesCount > 0) {
            const lastSeries = document.querySelector(`#categorie_selected_uniques_series_${seriesCount}`);
            if (lastSeries) {
                lastSeries.remove();
                seriesCount--;
            }
        }
    }

    // Ajout des écouteurs d'événements
    addButton.addEventListener('click', createNewSeries);
    removeButton.addEventListener('click', removeLastSeries);
});
