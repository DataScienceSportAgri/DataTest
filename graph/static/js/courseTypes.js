document.addEventListener('DOMContentLoaded', function () {
  // Fonction principale à exécuter
  function initializeCheckboxLogic() {
    const checkboxes = document.querySelectorAll('#course-types input[type="checkbox"]');
    const fouleeCheckbox = document.querySelector('input[value="Foulee"]');
    const routeCheckbox = document.querySelector('input[value="Course sur route"]');

    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', function () {
        const checkedBoxes = document.querySelectorAll('#course-types input[type="checkbox"]:checked');

        if (checkedBoxes.length > 2) {
          this.checked = false;
        } else if (checkedBoxes.length === 2) {
          if (!(fouleeCheckbox.checked && routeCheckbox.checked)) {
            this.checked = false;
          }
        }

        checkboxes.forEach(cb => {
          if (cb !== fouleeCheckbox && cb !== routeCheckbox) {
            cb.disabled = fouleeCheckbox.checked && routeCheckbox.checked;
          }
        });

        // Mettre à jour chartConfig.typeList
        window.chartConfig.typeList = Array.from(document.querySelectorAll('#course-types input[type="checkbox"]:checked')).map(cb => cb.value);
        console.log(window.chartConfig.typeList);
      });
    });
  }

  // Vérifier les modifications dans la div #course-types
  const targetNode = document.getElementById('course-types');
  if (targetNode) {
    // Observer les modifications dans la div
    const observer = new MutationObserver(() => {
      console.log('Modification détectée dans #course-types');
      initializeCheckboxLogic(); // Réinitialiser la logique si nécessaire
    });

    // Configurer l'observation des mutations
    observer.observe(targetNode, { childList: true, subtree: true });

    // Initialiser la logique au chargement initial
    initializeCheckboxLogic();
  } else {
    console.error("L'élément #course-types n'existe pas dans le DOM.");
  }
});
