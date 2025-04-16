document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('categorie');
    const loadingIndicator = document.getElementById('loading-indicator');
    const graphContainer = document.getElementById('vitesse-global');
    const graphDiv = graphContainer.querySelector('.js-plotly-plot') || graphContainer.firstChild;

    function updateVitesseChart(categorieId) {
    const params = new URLSearchParams({
        categorie: categorieId,
        ajax: true
    });

    fetch(`/graph/stat-global/?${params.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Erreur réseau');
        return response.json();
    })
    .then(data => {
        // 1. Mise à jour du titre
        Plotly.relayout(graphDiv, {
            'title.text': data.vitesse_plot_html.layout.title
        });

        // 2. Pour chaque type de distance (10km, Semi-marathon)
        for (const distanceName of ['10km', 'Semi-marathon']) {
            // Trouver les indices des traces correspondantes (ligne moyenne + zone d'écart)
            const traceIndex = Array.from(graphDiv.data).findIndex(
                trace => trace.name === distanceName
            );
            const areaIndex = Array.from(graphDiv.data).findIndex(
                trace => trace.name === `${distanceName} (écart-type)`
            );

            // Mettre à jour les traces si elles existent
            if (traceIndex !== -1 && data.vitesse_plot_html.data) {
                const traceData = data.vitesse_plot_html.data.find(t => t.name === distanceName);
                if (traceData) {
                    Plotly.update(graphDiv, {
                        x: [traceData.x],
                        y: [traceData.y]
                    }, {}, [traceIndex]);
                }
            }

            // Mettre à jour les zones d'écart-type
            if (areaIndex !== -1 && data.vitesse_plot_html.data) {
                const areaData = data.vitesse_plot_html.data.find(t => t.name === `${distanceName} (écart-type)`);
                if (areaData) {
                    Plotly.update(graphDiv, {
                        x: [areaData.x],
                        y: [areaData.y]
                    }, {}, [areaIndex]);
                }
            }
        }
    });
}

    // Détecter le changement de sélection
    categorySelect.addEventListener('change', function() {
        const selectedCategoryId = this.value;
        if (selectedCategoryId) {
            updateVitesseChart(selectedCategoryId);
        }
    });
});
