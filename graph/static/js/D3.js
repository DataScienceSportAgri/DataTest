function drawTrendLine(trendData) {
    const xScale = d3.scaleLinear().domain([minYear, maxYear]).range([0, width]);
    const yScale = d3.scaleLinear().domain([0, maxScore]).range([height, 0]);

    // Tracer la ligne de tendance
    svg.append("path")
        .datum(trendData)
        .attr("d", d3.line()
            .x(d => xScale(d.date))
            .y(d => yScale(d.trend))
        )
        .attr("stroke", "#d62728")
        .attr("stroke-width", 2);

    // Afficher l'équation à droite
    svg.append("text")
        .attr("x", width - 10)
        .attr("y", 20)
        .attr("text-anchor", "end")
        .style("font-size", "12px")
        .text(`Tendance groupe : y = ${avgSlope.toFixed(2)}x + ${avgIntercept.toFixed(2)}`);
}

function generateConfidenceArea(trend, confidence, xScale, yScale) {
    const areaPoints = [];
    const steps = 50; // Plus de points pour une courbe plus lisse
    const step = (trend.max_year - trend.min_year) / steps;

    for (let x = trend.min_year; x <= trend.max_year; x += step) {
        const y = trend.slope * x + trend.intercept;
        areaPoints.push({
            x: xScale(x),
            y0: yScale(y - confidence),
            y1: yScale(y + confidence)
        });
    }

    return areaPoints;
}


document.addEventListener('DOMContentLoaded', function() {
    const dataElement = document.getElementById('series-data');
    if (!dataElement) {
        console.error("Élément 'series-data' introuvable !");
        return;
    }

    const seriesData = JSON.parse(dataElement.textContent);

    const margin = {top: 40, right: 30, bottom: 40, left: 100};
    const width = 1250 - margin.left - margin.right;
    const height = 700 - margin.top - margin.bottom;

    // Création du conteneur SVG
    const svg = d3.select(".graph-container")
      .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);

    // Groupe principal pour le zoom/pan
    const mainGroup = svg.append("g")
        .attr("class", "plot-area")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Outil de tooltip
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background", "#fff")
      .style("padding", "8px")
      .style("border", "1px solid #ddd");

    function drawGraph(data) {
        const dataType = data[0].type || "individual";

    // Déclarer les variables d'échelle au niveau de la fonction
    let xScale, yScale, allDates, allScores, score;
        if (dataType === "individual") {
            // Filtrer les données individuelles AVANT de calculer les dates/scores
            const individualData = data.filter(d => d.type === "individual");
            console.log("Filtered individual data:", individualData);
                    // Définir les échelles

            // Log data counts by type
            console.log("Data count by type:", {
                total: data.length,
                individual: data.filter(d => d.type === "individual").length,
                trend: data.filter(d => d.type === "trend").length
            });

            // Calculer les domaines uniquement sur les données individuelles
            const allDates = individualData.flatMap(d => d.values.map(v => v.date));
            const allScores = individualData.flatMap(d => d.values.map(v => v.score));

            xScale = d3.scaleLinear()
                .domain(d3.extent(allDates))
                .range([0, width]);

            yScale = d3.scaleLinear()
                .domain([0, d3.max(allScores)])
                .range([height, 0]);
            // Générateur de lignes
            const lineGenerator = d3.line()
                .x(d => xScale(d.date))
                .y(d => yScale(d.score))
                .curve(d3.curveMonotoneX);

                    // 1. Extraire les tendances séparément
        const trends = data.filter(d => d.type === "trend");
        console.log("Trend data found:", trends);

        // 2. Regrouper les séries individuelles par groupe
        const groupedData = d3.groups(individualData, d => d.groupe_safe);
// 4. DESSINER LES TENDANCES AVEC DES STYLES DISTINCTS
        // Définir des styles distincts pour chaque tendance
        const dashPatterns = ["4 2", "8 4", "2 2", "1 1"];
        const strokeWidths = [2, 2.5, 3, 3.5];

        // Dessiner chaque tendance
        trends.forEach((trend, i) => {
            score = trend.score
            // Vérifier les propriétés essentielles
            if (trend.slope === undefined || trend.intercept === undefined) {
                console.error(`Missing slope/intercept for trend ${i}:`, trend);
                return;
            }

            // Calculer les points de début et fin de la tendance
            const yStart = trend.slope * trend.min_year + trend.intercept;
            const yEnd = trend.slope * trend.max_year + trend.intercept;

            console.log(`Trend ${i} points:`, {
                start: {x: trend.min_year, y: yStart},
                end: {x: trend.max_year, y: yEnd}
            });

            // Tracer la ligne de tendance avec un style distinct
            mainGroup.append("line")
                .attr("class", `trend-line-${i}`)
                .attr("x1", xScale(trend.min_year))
                .attr("y1", yScale(yStart))
                .attr("x2", xScale(trend.max_year))
                .attr("y2", yScale(yEnd))
                .attr("stroke", trend.color)
                .attr("stroke-width", strokeWidths[i % strokeWidths.length])
                .attr("stroke-dasharray", dashPatterns[i % dashPatterns.length]);

            // Ajouter la zone de confiance si disponible
            if (trend.group_variance) {
                const confidence = 1.96 * Math.sqrt(trend.group_variance);
                console.log(`Confidence interval for trend ${i}:`, confidence);

                mainGroup.append("path")
                    .datum(generateConfidenceArea(trend, confidence, xScale, yScale))
                    .attr("class", `confidence-area-${i}`)
                    .attr("d", d3.area()
                        .x(d => d.x)
                        .y0(d => d.y0)
                        .y1(d => d.y1)
                    )
                    .attr("fill", trend.color)
                    .attr("fill-opacity", 0.1);
            }

            // Afficher l'équation avec décalage vertical pour éviter les chevauchements
            mainGroup.append("text")
                .attr("class", `trend-equation-${i}`)
                .attr("x", width - 10)
                .attr("y", yScale(yEnd) - 20 - (i * 25)) // Décalage pour chaque équation
                .attr("text-anchor", "end")
                .style("font-size", "12px")
                .style("fill", trend.color)
                .html(`y = ${trend.slope.toFixed(2)}x <tspan dx="-0.5em" dy="1.2em">+ ${trend.intercept.toFixed(2)}</tspan>`);

            // Confirmer que la tendance a bien été tracée
            console.log(`Trend ${i} drawn with color ${trend.color}`);
        });
        // 3. Dessiner chaque groupe de séries dans son propre conteneur
        groupedData.forEach(([groupe, series]) => {
            // Créer un conteneur de groupe qui sera réactif au survol
            const groupContainer = mainGroup.append("g")
                .attr("class", `group-${groupe}`)
                .style("opacity", 0.1)  // Faible opacité initiale
                .on("mouseover", function() {
                    d3.select(this).transition().duration(200).style("opacity", 0.5);
                })
                .on("mouseout", function() {
                    d3.select(this).transition().duration(200).style("opacity", 0.1);
                });

            // Dessiner toutes les séries du groupe à l'intérieur du conteneur
            groupContainer.selectAll(".series")
                .data(series)
                .enter().append("path")
                .attr("class", "series")
                .attr("d", d => lineGenerator(d.values))
                .style("stroke", d => d.color)
                .style("fill", "none")
                .on("mouseover", function(event, d) {
                    // Mettre en évidence la série survolée
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .style("stroke-width", 4)
                        .style("opacity", 1);

                    // Afficher le label du coureur
                    const lastPoint = d.values[d.values.length - 1];
                    mainGroup.append("text")
                        .attr("class", "hover-label")
                        .attr("x", xScale(lastPoint.date))
                        .attr("y", yScale(lastPoint.score) - 10)
                        .attr("text-anchor", "middle")
                        .attr("fill", d.color)
                        .style("font-weight", "bold")
                        .text(`${d.prenom_marsien || d.prenom || ""} " " ${d.nom_marsien || d.nom || ""}`);
                })
                .on("mouseout", function() {
                    // Restaurer l'apparence normale
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .style("stroke-width", 2)
                        .style("opacity", 1);

                    // Supprimer le label
                    mainGroup.selectAll(".hover-label").remove();
                });
        });



        } else {
            // Traitement des nuages de points et lignes de tendance (coureur_type='tous')
            const pointSeries = data.filter(d => d.type === "group");
            const trendSeries = data.filter(d => d.type === "trend");

            allDates = pointSeries.flatMap(d => d.points.map(p => p.date));
            allScores = pointSeries.flatMap(d => d.points.map(p => p.score));

            xScale = d3.scaleLinear()
                .domain(d3.extent(allDates))
                .range([0, width]);

            yScale = d3.scaleLinear()
                .domain([0, d3.max(allScores)])
                .range([height, 0]);



            // Affichage des tendances et équations
            trendSeries.forEach(trend => {
                score = trend.score
                // Ligne de tendance
                mainGroup.append("line")
                    .attr("x1", xScale(trend.min_year))
                    .attr("y1", yScale(trend.slope * trend.min_year + trend.intercept))
                    .attr("x2", xScale(trend.max_year))
                    .attr("y2", yScale(trend.slope * trend.max_year + trend.intercept))
                    .attr("stroke", trend.color)
                    .attr("stroke-width", 2)
                    .attr("stroke-dasharray", "4 2")
                    .attr("opacity", 0.9);

                // Équation de la droite affichée
                mainGroup.append("text")
                    .attr("x", width - 10)
                    .attr("y", yScale(trend.slope * ((trend.min_year + trend.max_year) / 2) + trend.intercept) - 15)
                    .attr("text-anchor", "middle")
                    .attr("fill", trend.color)
                    .style("font-size", "12px")
                    .style("font-style", "italic")
                    .text(`y = ${trend.slope.toFixed(2)}x + ${trend.intercept.toFixed(2)}`);

                // Zone de confiance
                if (trend.residual_std) {
                    const confidence = 1.96 * trend.residual_std;
                    const areaData = [];
                    for (let x = trend.min_year; x <= trend.max_year; x += 1) {
                        const y = trend.slope * x + trend.intercept;
                        areaData.push({
                            x: xScale(x),
                            y0: yScale(y - confidence),
                            y1: yScale(y + confidence)
                        });
                    }
                    const areaGenerator = d3.area()
                        .x(d => d.x)
                        .y0(d => d.y0)
                        .y1(d => d.y1);

                    mainGroup.append("path")
                        .datum(areaData)
                        .attr("d", areaGenerator)
                        .attr("fill", trend.color)
                        .attr("fill-opacity", 0.2)
                        .attr("stroke", "none");
                }
            });
            // Dessiner les points (scatter plot)
            pointSeries.forEach(series => {
                // Filtrer les points valides (avec score et date)
                const validPoints = series.points.filter(p => !isNaN(p.date) && !isNaN(p.score));
                mainGroup.selectAll(`.point-${series.groupe_safe}`)
                    .data(validPoints)
                    .enter().append("circle")
                    .attr("class", `point-${series.groupe_safe}`)
                    .attr("cx", d => xScale(d.date))
                    .attr("cy", d => yScale(d.score))
                    .attr("r", 3)
                    .style("fill", series.color)
                    .style("opacity", 0.6)
                    .on("mouseover", function(event, d) {
                        tooltip.transition()
                            .duration(200)
                            .style("opacity", 0.9);

                        tooltip.html(`
                            <strong>${d.prenom_marsien || d.prenom || ""} ${d.nom_marsien || d.nom || ""}</strong><br>
                            Date: ${d.date}<br>
                            Score: ${d.score.toFixed(2)}
                        `)
                        .style("left", `${event.pageX + 10}px`)
                        .style("top", `${event.pageY - 28}px`);

                        d3.select(this)
                            .transition()
                            .style("opacity", 1)
                            .attr("r", 5);
                    })
                    .on("mouseout", function() {
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0);

                        d3.select(this)
                            .transition()
                            .style("opacity", 0.6)
                            .attr("r", 3);
                    });
            });
        }



        mainGroup.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(xScale).tickFormat(d3.format("d")));

        mainGroup.append("g")
            .attr("class", "y-axis")
            .call(d3.axisLeft(yScale));

        // Labels des axes
        mainGroup.append("text")
            .attr("class", "x label")
            .attr("text-anchor", "middle")
            .attr("x", width / 2)
            .attr("y", height + 35)
            .text("Année");

        mainGroup.append("text")
            .attr("class", "y label")
            .attr("text-anchor", "middle")
            .attr("transform", `rotate(-90)`)
            .attr("x", -height / 2)
            .attr("y", -45)
            .text(`Score de performance ${score}`);
    }

    // Fonction zoom/pan
    const zoom = d3.zoom()
        .scaleExtent([1, 8])
        .on("zoom", (event) => {
            mainGroup.attr("transform", `translate(${event.transform.x + margin.left},${event.transform.y + margin.top}) scale(${event.transform.k})`);
        });

    svg.call(zoom);
    function fetchAndUpdateGraph() {
        // Récupère les valeurs sélectionnées
        const scoreType = document.querySelector('input[name="scoreType"]:checked').value;
        const performanceTier = document.querySelector('input[name="performanceTier"]:checked').value;
        const cohortType = document.querySelector('input[name="cohortType"]:checked').value;
        const action = 'submit'
        const graph = 'graph2'

        // Fait une requête AJAX GET vers la vue Django avec les paramètres
        fetch(`/graph/score-distribution/?scoreType=${scoreType}&performanceTier=${performanceTier}&cohortType=${cohortType}&action=${action}&graph=${graph}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(newData => {
            // Nettoie le graphique avant de le redessiner
            mainGroup.selectAll("*").remove();
            drawGraph(newData.response_data || newData); // selon la structure du JSON retourné
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du graphique:', error);
        });
    }

    // Ajoute l'écouteur à tous les boutons radio du formulaire
    document.querySelectorAll('#scoreFormRight input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', fetchAndUpdateGraph);
    });
    // Initialiser le graphique
    drawGraph(seriesData);
});
