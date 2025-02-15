document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById("categorieSimplifieeButton");

     // Récupérer l'URL actuelle
    const url = new URL(window.location.href); // Corrigé : Utiliser "URL" au lieu de "URLa"
    const currentMode = url.searchParams.get("mode");

    // Initialiser le texte du bouton en fonction du mode actuel
    if (currentMode === "simplifie") {
        button.textContent = "Passer en mode Catégories Classiques";
        window.chartConfig.mode = 'simplifie' ; // Initialisation pour d'autres scripts éventuels
    } else {
        button.textContent = "Passer en mode Catégories Simplifiées";
        window.chartConfig.mode = 'classique' ; // Initialisation pour d'autres scripts éventuels
    }

    // Initialiser le texte du bouton en fonction du mode actuel
    if (currentMode === "simplifie") {
        button.textContent = "Passer en mode Catégories Classiques";
        window.chartConfig.mode = 'simplifie' ; // Initialisation pour d'autres scripts éventuels
    } else {
        button.textContent = "Passer en mode Catégories Simplifiées";
        window.chartConfig.mode = 'classique' ; // Initialisation pour d'autres scripts éventuels
    }

    // Ajouter un gestionnaire d'événement pour le clic sur le bouton
    button.addEventListener("click", function () {
        console.log("Bouton de changement de catégorie cliqué");

        // Arrêter les mises à jour automatiques (si applicable)
        console.log("Arrêt des mises à jour automatiques");
        window.isRefreshing = true;

        // Arrêter le compte à rebours (si présent)
        const countdownElement = document.getElementById('countdown');
        if (countdownElement) {
            countdownElement.innerHTML = ''; // Réinitialiser l'affichage du compte à rebours
            console.log("Compte à rebours arrêté");
        }

        // Basculer entre les modes
        if (currentMode === "simplifie") {
            url.searchParams.set("mode", "classique");
            this.textContent = "Passer en mode Catégories Simplifiées";
            window.chartConfig.mode = 'classique';
        } else {
            url.searchParams.set("mode", "simplifie");
            this.textContent = "Passer en mode Catégories Classiques";
            window.chartConfig.mode = 'simplifie';
        }
        console.log('window.chartConfig',window.chartConfig)
        // Rediriger vers la nouvelle URL
        console.log("Redirection vers :", url.toString());
        window.location.href = url.toString();
    });
});
