document.addEventListener("DOMContentLoaded", function () {
    let rotationY = -0.002;
    let rotationX = -0.0001;
    let rotationZ = 0.00015;
    const infoBox = document.getElementById("infoBox");
    let isLocked = false; // Empêche les interactions pendant le délai
    let isCentered = false; // Indique si la box est centrée ou non
    window.slowDownMarsRotation = slowDownMarsRotation;
    // Fonction pour déplacer la box au centre
    function moveToCenter() {
        if (!isLocked && !isCentered) {
            slowDownMarsRotation();
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

function slowDownMarsRotation() {
    if (!model) return; // Sécurité

    // Sauvegarde les valeurs initiales
    const originalY = rotationY;
    const originalX = rotationX;
    const originalZ = rotationZ;

    // Ralentir la rotation Y
    rotationY = originalY * 0.2;

    // Modifie légèrement X et Z de façon aléatoire
    rotationX = originalX + (Math.random() - 0.5) * 0.0002; // variation très légère
    rotationZ = originalZ + (Math.random() - 0.5) * 0.0002;

    // Après 2 secondes, remet les valeurs initiales
    setTimeout(() => {
        rotationY = originalY;
        rotationX = originalX;
        rotationZ = originalZ;
    }, 2600);
}
