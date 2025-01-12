document.addEventListener('DOMContentLoaded', function() {
    const rawData = document.getElementById('categories').textContent;
const categoriesData = JSON.parse(JSON.parse(rawData));

console.log('Double parsed data:', categoriesData);
console.log('Is array after double parsing:', Array.isArray(categoriesData));
    const allCategorieDiv = document.getElementById('all_categorie');
    const selectedCategorieDiv = document.getElementById('categorie_selected');

    for (const category of categoriesData) {
        if (category.sexe !== 'F' && category.sexe !== 'M') {
                const box = document.createElement('div');
                box.className = 'category-box';
                box.draggable = true;
                box.textContent = category.nom;  // Utiliser category.nom au lieu de category
                box.dataset.sexe = category.sexe; // Conserver l'information du sexe
                allCategorieDiv.appendChild(box);

                box.addEventListener('dragstart', dragStart);
            }
        }

    allCategorieDiv.addEventListener('dragover', dragOver);
    allCategorieDiv.addEventListener('drop', drop);
    selectedCategorieDiv.addEventListener('dragover', dragOver);
    selectedCategorieDiv.addEventListener('drop', drop);

    function dragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.textContent);
    }

    function dragOver(e) {
        e.preventDefault();
    }

function drop(e) {
    e.preventDefault();
    const data = e.dataTransfer.getData('text');
    const draggedElement = Array.from(document.querySelectorAll('.category-box')).find(el => el.textContent.trim() === data);
    if (draggedElement && e.target.classList.contains('category-container')) {
        e.target.appendChild(draggedElement);
    }
    updateSelectedCategories();
}


    function updateSelectedCategories() {
        const selectedCategories = Array.from(selectedCategorieDiv.children).map(box => box.textContent);
        console.log('Catégories sélectionnées:', selectedCategories);
        // Vous pouvez utiliser 'selectedCategories' comme variable pour votre eventListener 'selectcategories'
    }
});

