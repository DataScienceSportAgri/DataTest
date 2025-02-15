document.addEventListener("DOMContentLoaded", function () {
    const infoBox = document.getElementById("infoBox");
    let isLocked = false; // Empêche les interactions pendant le délai
    let isCentered = false; // Indique si la box est centrée ou non

    // Fonction pour déplacer la box au centre
    function moveToCenter() {
        if (!isLocked && !isCentered) {
            isLocked = true; // Bloque les interactions
            infoBox.classList.remove("initial");
            infoBox.classList.add("centered");
            isCentered = true;

            // Débloque après un délai de 2 secondes
            setTimeout(() => {
                isLocked = false;
            }, 2000);
        }
    }

    // Fonction pour retourner à la position initiale
    function moveToInitial() {
        if (!isLocked && isCentered) {
            isLocked = true; // Bloque les interactions
            infoBox.classList.remove("centered");
            infoBox.classList.add("initial");
            isCentered = false;

            // Débloque après un délai de 2 secondes
            setTimeout(() => {
                isLocked = false;
            }, 500);
        }
    }

    // Gestion du survol de la souris
    infoBox.addEventListener("mouseenter", function () {
        if (!isCentered) {
            moveToCenter(); // Passe au centre si en position initiale
        } else {
            moveToInitial(); // Retourne à l'origine si déjà centré
        }
    });
});