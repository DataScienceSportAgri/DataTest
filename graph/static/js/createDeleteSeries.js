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

    // Conteneur pour le titre éditable et le bouton de suppression
    const headerContainer = document.createElement('div');
    headerContainer.style.display = 'flex';
    headerContainer.style.justifyContent = 'space-between';
    headerContainer.style.alignItems = 'center';
    headerContainer.style.marginBottom = '10px';
    // Positionnement du titre en haut à gauche avec une marge
    headerContainer.style.position = 'relative'; // Permet d'utiliser top et left
    headerContainer.style.top = '5px'; // 5px depuis le haut
    headerContainer.style.left = '5px'; // 5px depuis la gauche

    // Champ d'édition du titre
    const seriesTitleInput = document.createElement('input');
    seriesTitleInput.type = 'text';
    seriesTitleInput.value = title || `Série ${seriesCount}`;
    // Ajout d'une classe commune
    seriesTitleInput.classList.add('titre-serie');

    // Styles pour ressembler à un <h4>
    seriesTitleInput.style.fontSize = '1.5em'; // Taille similaire à <h4>
    seriesTitleInput.style.fontWeight = 'bold'; // Gras comme un titre
    seriesTitleInput.style.border = 'none'; // Pas de bordure pour ressembler à un texte
    seriesTitleInput.style.outline = 'none'; // Pas de contour lors du focus
    seriesTitleInput.style.backgroundColor = 'transparent'; // Fond transparent
    seriesTitleInput.style.width = '100%'; // Occupe toute la largeur disponible
    seriesTitleInput.style.marginRight = '10px'; // Ajustement de l'espacement
    seriesTitleInput.style.padding = '0'; // Pas de padding pour ressembler à un texte brut

        // Bouton pour supprimer la série
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Supprimer';
    deleteButton.style.backgroundColor = '#ff4d4d'; // Couleur rouge pour indiquer une action destructive
    deleteButton.style.color = '#fff';
    deleteButton.style.border = 'none';
    deleteButton.style.padding = '5px 10px';
    deleteButton.style.cursor = 'pointer';
        // Ajout des éléments au conteneur d'en-tête
    headerContainer.appendChild(seriesTitleInput);
    headerContainer.appendChild(deleteButton);
    newSeriesDiv.appendChild(headerContainer);


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

    // Gestion du bouton de suppression
    deleteButton.addEventListener('click', function () {
        // Renvoyer les éléments "draggable" dans la boîte all-categories
        const draggableElements = newSeriesDiv.querySelectorAll('.category-box');
        draggableElements.forEach(box => {
            allCategorieDiv.appendChild(box);
        });

        // Supprimer la série
        container.removeChild(newSeriesDiv);
        });
}
function removeLastSeries() {
    if (seriesCount > 2) {  // Ne supprime pas les séries F et M
        const lastSeries = document.querySelector(`#categorie_selected_uniques_series_${seriesCount}`);
        const draggableElements = newSeriesDiv.querySelectorAll('.category-box');
        draggableElements.forEach(box => {
            allCategorieDiv.appendChild(box);
        });
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
