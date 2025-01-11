console.log(window.isRefreshing);
console.log('chart_update.js loaded');


// Vous pouvez maintenant utiliser updateCountdown dans ce fichier
function waitForChartConfig() {
        if (window.chartConfig && window.chartConfig.refreshInterval !== null) {
            console.log('ChartConfig loaded:', window.chartConfig);
            // Ici, vous pouvez appeler vos fonctions qui dépendent de chartConfig
        } else {
            console.log('Waiting for chartConfig...');
            setTimeout(waitForChartConfig, 50);
        }
    }
    let countdownIntervalId = null;




// Fonction de mise à jour
function updateGraph(newData) {
    if (!newData || !newData.data || !newData.layout) {
        console.error('Invalid newData object', newData);
        return;
    }

    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) {
        console.error('chart-container element not found');
        return;
    }

    if (typeof Plotly !== 'undefined') {
        console.log("Plotly est correctement chargé");
        Plotly.react('chart-container', newData.data, newData.layout);
    } else {
        console.error("Plotly n'est pas chargé correctement");
    }
}

function fetchUpdates() {
    window.isRefreshing = true;
    console.log('Sending update request to server');
    const url = new URL(window.location.href);
    url.searchParams.set('action', 'update');

    if (window.chartConfig && window.chartConfig.minDistance !== undefined) {
        url.searchParams.set('min_distance', window.chartConfig.minDistance);
    }
    if (window.chartConfig && window.chartConfig.maxDistance !== undefined) {
        url.searchParams.set('max_distance', window.chartConfig.maxDistance);
    }
    if (window.chartConfig && window.chartConfig.loadedCount !== undefined) {
        url.searchParams.set('loaded_count', window.chartConfig.loadedCount);
    }

    return fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        updateGraph(data.plot_data);

        if (data.is_update) {
            document.getElementById('loaded-count').textContent = data.loaded_count;
            document.getElementById('total-count').textContent = data.total_count;
            window.chartConfig.loadedCount = data.loaded_count;
            window.chartConfig.totalCount = data.total_count;
        } else {
            document.getElementById('loaded-count').textContent = window.chartConfig.loadedCount;
            document.getElementById('total-count').textContent = window.chartConfig.totalCount;
        }
    }).finally(() => {
        window.isRefreshing = false;
    });
}





document.addEventListener('DOMContentLoaded', () => {
    console.log('Setting up periodic updates');
    console.log('info' + window.chartConfig.refreshInterval);

    // Start countdown and fetchUpdates when countdown hits 0
    updateCountdown({
        countdown: Math.floor(window.chartConfig.refreshInterval / 1000),
        message: "Prochaine mise à jour dans {seconds} secondes"
    }, document.getElementById('countdown'), fetchUpdates);  // Pass fetchUpdates as the callback
});