document.addEventListener('DOMContentLoaded', function() {
    // Références DOM
    const forml = document.getElementById('scoreFormLeft');
    // Solution plus robuste
    const graphContainer = document.getElementById('graph-1-container');
    const global = document.getElementById('graph-wrapper')
    const graphDiv = graphContainer.querySelector('.js-plotly-plot') || graphContainer.firstChild;
    let currentData = [];
    let refreshInterval;

    // Gestionnaires d'événements
    function handleFormChange(e) {
        if (e.target.name === 'scoreType') {
            updateGraphType(e.target.value);
        }
    }

    // Fonctions principales
    async function updateGraphType(scoreType) {
        const params = new URLSearchParams({
        score_type: scoreType,
        action: 'submit',
            graph: 'graph1'
            });
        try {
            fetch(`/graph/score-distribution/?${params.toString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).then(response => {
            if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
            return response.json(); // Changez ici pour récupérer les données JSON
            })
            .then(
                data => { // data contiendra l'objet JSON
                    if (data.html) {
                        console.log('HTML reçu', data.html);
                            graphContainer.innerHTML = ''
                            global.innerHTML = data.html
                    }
                });
        } catch (error) {
            console.error('Error:', error);
        }
    }
    // 1. Fonction qui attend que le graphique soit prêt
    function waitForPlotlyGraph() {
        return new Promise((resolve) => {
            // Solution plus robuste
        const graphContainer = document.getElementById('graph-container');
        const graphDiv = graphContainer.querySelector('.js-plotly-plot') || graphContainer.firstChild;

            // Si le graphique est déjà initialisé
            if (graphDiv && graphDiv._fullLayout) {
                graphReady = true;
                return resolve(graphDiv);
            }

            // Sinon, utiliser un écouteur d'événement Plotly
            const checkGraph = () => {
                // Solution plus robuste
                    const graphContainer = document.getElementById('graph-container');
                    const graphElement = graphContainer.querySelector('.js-plotly-plot') || graphContainer.firstChild;
                if (graphElement && graphElement._fullLayout) {
                    graphReady = true;
                    observer.disconnect(); // Arrêter l'observation
                    clearInterval(checkInterval); // Arrêter la vérification périodique
                    resolve(graphElement);
                }
            };

            // Observer les mutations du DOM pour détecter les changements dans le conteneur
            const observer = new MutationObserver(checkGraph);
            observer.observe(graphContainer, { childList: true, subtree: true });

            // En parallèle, vérifier régulièrement l'état (approche par sondage)
            const checkInterval = setInterval(checkGraph, 500);

            // Définir un timeout pour éviter d'attendre indéfiniment
            setTimeout(() => {
                observer.disconnect();
                clearInterval(checkInterval);
                console.warn("Timeout en attendant l'initialisation du graphique");
                resolve(null); // Résoudre avec null en cas de timeout
            }, 10000);
        });
    }

    async function refreshData() {
        try {
            // 1. Ajouter l'en-tête X-Requested-With
            const response = await fetch('', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

        const responseData = await response.json();

            if (!responseData || !responseData.new_data || !responseData.new_data.extend_data) {
                console.error('Format de données invalide', responseData);
                return;
            }

            console.log('Nouvelles données:', responseData.new_data);
            // Solution plus robuste
            const graphContainer = document.getElementById('graph-1-container');
            const graphDiv = graphContainer.querySelector('.js-plotly-plot') || graphContainer.firstChild;
            // Ajouter avant la boucle de recherche
            if (graphDiv && graphDiv.data) {
                console.log("Traces disponibles:", graphDiv.data.map(trace => trace.name));
            }
           // Pour chaque sexe
        for (const sexe of ['M', 'F']) {
            const sexeData = responseData.new_data.plot_data[`contour_${sexe}`];
            if (!sexeData) continue;

            // Trouver l'indice de la trace de points pour ce sexe
            const scatterIndex = Array.from(graphDiv.data).findIndex(
                trace => trace.name === `Densité ${sexe}` || trace.name === sexe
            );
            console.log(`Indice de la trace pour ${sexe}:`, scatterIndex);

            // Vérifier que l'indice est valide et définir la trace
            if (scatterIndex !== -1) {
                const trace = graphDiv.data[scatterIndex];

                if (trace.type === 'histogram2dcontour') {
                    // Utiliser des parenthèses pour établir une priorité d'évaluation correcte
                    // Au lieu d'essayer de combiner les tableaux:
                    Plotly.deleteTraces(graphDiv, scatterIndex);
                    Plotly.addTraces(graphDiv, {
                        type: 'histogram2dcontour',
                        x: sexeData.x,  // Utiliser uniquement les nouvelles données
                        y: sexeData.y,
                        colorscale: trace.colorscale,
                        name: trace.name,
                        showscale: trace.showscale,
                        contours: trace.contours,
                        line: trace.line
                    }, scatterIndex);

                    console.log(`Contour pour ${sexe} mis à jour avec ${sexeData.x.length} points`);
                }
            }
            // MISE À JOUR DES ÉQUATIONS DE TENDANCE
            // Récupérer les données de tendance
            const trendData = responseData.new_data.plot_data[`trend_${sexe}`];

            if (trendData) {
                // Trouver l'indice de la trace de tendance pour ce sexe
                const trendIndex = Array.from(graphDiv.data).findIndex(
                    trace => trace.name && trace.name.startsWith(`${sexe}: y =`)
                );

                if (trendIndex !== -1) {
                    // Calculer les points de la droite à partir des coefficients
                    const minYear = responseData.new_data.min_year;
                    const maxYear = responseData.new_data.max_year;
                    const slope = trendData.slope;
                    const intercept = trendData.intercept;
                    const r_squared = trendData.r_squared;

                    // Formater l'équation (similaire à celle affichée dans la légende)
                    const equationString = `${sexe}: y = ${slope.toFixed(3)}x + ${intercept.toFixed(3)}, R² = ${r_squared.toFixed(3)}`;

                    // Mettre à jour la trace de tendance
                    Plotly.update(graphDiv, {
                        // Mettre à jour les données de la droite
                        x: [[minYear, maxYear]],
                        y: [[slope * minYear + intercept, slope * maxYear + intercept]],
                        // Mettre à jour le nom avec la nouvelle équation
                        name: [equationString]
                    }, {}, [trendIndex]);

                    console.log(`Équation de tendance mise à jour pour ${sexe}: ${equationString}`);

                }
            }
        }


        } catch (error) {
            console.error('Erreur lors du rafraîchissement:', error);
        }
    }

        // Initialisation
        function init() {
            forml.addEventListener('change', handleFormChange);
            refreshInterval = setInterval(refreshData, 25000);
            // Retirez l'appel initial à updateGraphType ici pour éviter son exécution automatique
    }

    init();
});
