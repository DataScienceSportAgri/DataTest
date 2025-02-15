const countdownElement = document.getElementById('countdown');

// Variable globale pour stocker l'ID du setTimeout
window.countdownTimeoutId = null;

// Fonction pour arrêter le compte à rebours existant
window.stopExistingCountdown = function () {
    if (window.countdownTimeoutId) {
        clearTimeout(window.countdownTimeoutId);
        window.countdownTimeoutId = null;
    }
}


window.updateCountdown = function(countdown, targetElement, onComplete) {
    if (!countdown || typeof countdown.message !== 'string' || typeof countdown.countdown !== 'number') {
        console.error('Invalid countdown object');
        return;
    }

    let seconds = countdown.countdown;

    if (!targetElement) {
        targetElement = document.getElementById('countdown');
        if (!targetElement) {
            console.error("Élément 'countdown' non trouvé dans le document");
            return;
        }
    }

    stopExistingCountdown();

    if ((targetElement.textContent == "Chargement terminé") & (window.chartConfig.loadedCount == window.chartConfig.totalCount)) {
        return;
    }

    const updateText = () => {
        if (window.isRefreshing) {
            targetElement.textContent = "Mise à jour en cours...";
            // Attendre que isRefreshing devienne false avant de continuer
            window.countdownTimeoutId = setTimeout(updateText, 0);
            return;
        }

        if (seconds > 0) {
            targetElement.textContent = countdown.message.replace('{seconds}', seconds);
            seconds--;
            window.countdownTimeoutId = setTimeout(updateText, 1000);
        } else {
            targetElement.textContent = "Mise à jour en cours...";
            window.isRefreshing = true;

            if (onComplete && typeof onComplete === 'function') {

                onComplete().then(() => {
                        if (window.chartConfig.loadedCount < window.chartConfig.totalCount) {
                            seconds = countdown.countdown;
                            window.countdownTimeoutId = setTimeout(updateText, 0); }
                        else {
                            targetElement.textContent = "Chargement terminé";
                            stopExistingCountdown();
                            }
                        }).catch(error => {
                            seconds = countdown.countdown;
                            window.countdownTimeoutId = setTimeout(updateText, 0);
                    })


                }
            }
        };

    window.countdownTimeoutId = setTimeout(updateText, 0);
};