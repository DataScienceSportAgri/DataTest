document.addEventListener('DOMContentLoaded', function() {
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
        const seriesName = seriesDiv.querySelector('h4').textContent;
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


function createInitialSeries() {
    createSeriesWithTitle('F');
    createSeriesWithTitle('M');
    window.chartConfig.seriesCategories = updateSeriesCategories();
}

    function dragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.textContent);
    }

function createSeriesWithTitle(title) {
    seriesCount++;
    const newSeriesDiv = document.createElement('div');
    newSeriesDiv.className = 'category-container';
    newSeriesDiv.id = `categorie_selected_uniques_series_${seriesCount}`;

        // Ajoutez ces styles
    newSeriesDiv.style.width = '550px'; // Ajustez selon vos besoins
    newSeriesDiv.style.flexShrink = '0';
    newSeriesDiv.style.marginBottom = '10px';

    const seriesTitle = document.createElement('h4');
    seriesTitle.textContent = title || `Série ${seriesCount}`;
    newSeriesDiv.appendChild(seriesTitle);

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
}
function removeLastSeries() {
    if (seriesCount > 2) {  // Ne supprime pas les séries F et M
        const lastSeries = document.querySelector(`#categorie_selected_uniques_series_${seriesCount}`);
        if (lastSeries) {
            lastSeries.remove();
            seriesCount--;
        }
    }
}


addButton.addEventListener('click', () => {
    createSeriesWithTitle();
    window.chartConfig.seriesCategories = updateSeriesCategories();
});

removeButton.addEventListener('click', () => {
    removeLastSeries();
    window.chartConfig.seriesCategories = updateSeriesCategories();
});

});
