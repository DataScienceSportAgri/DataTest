function generateStatsDivs(categories, stats) {
    const container = document.getElementById('dynamic-stats-container');
    container.innerHTML = ''; // Vider le conteneur

    categories.forEach(category => {
        const div = document.createElement('div');
        div.className = 'stats-flex-container';
        div.innerHTML = `
            <div class="stats-section">
                <h4>${category}</h4>
                <table>
                    <tr><td>Moyenne :</td><td>${stats[category].moyenne.toFixed(2)} km/h</td></tr>
                    <tr><td>Écart-type :</td><td>${stats[category].ecart_type.toFixed(2)} km/h</td></tr>
                    <tr><td>Variance :</td><td>${stats[category].variance.toFixed(2)} (km/h)²</td></tr>
                    <tr><td>% Variance :</td><td>${stats[category].pourcentage_variance.toFixed(2)}%</td></tr>
                    <tr><td>% Écart-type :</td><td>${stats[category].pourcentage_ecart_type.toFixed(2)}%</td></tr>
                    <tr><td>Skewness :</td><td>${stats[category].skewness.toFixed(3)}</td></tr>
                    <tr><td>Kurtosis :</td><td>${stats[category].kurtosis.toFixed(3)}</td></tr>
                </table>
            </div>
        `;
        container.appendChild(div);
    });
}
