document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById("categorieSimplifieeButton");

    button.addEventListener("click", function () {
        console.log("Bouton de changement de catégorie cliqué");

        // Arrêter les mises à jour automatiques
        console.log("Arrêt des mises à jour automatiques");
        window.isRefreshing = true;

        // Arrêter le compte à rebours
        const countdownElement = document.getElementById('countdown');
        if (countdownElement) {
            countdownElement.innerHTML = ''; // Réinitialiser l'affichage du compte à rebours
            console.log("Compte à rebours arrêté");
        }

        // Récupérer l'URL actuelle
        const url = new URL(window.location.href);

        // Basculer entre les modes
        const currentMode = url.searchParams.get("mode");
        if (currentMode === "simplifie") {
            url.searchParams.set("mode", "classique");
            this.textContent = "Passer en mode Catégories Simplifiées";
        } else {
            url.searchParams.set("mode", "simplifie");
            this.textContent = "Passer en mode Catégories Classiques";
        }

        // Rediriger vers la nouvelle URL
        console.log("Redirection vers :", url.toString());
        window.location.href = url.toString();
    });
});