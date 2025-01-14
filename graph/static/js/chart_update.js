console.log(window.isRefreshing);
console.log('chart_update.js loaded');

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}



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

    if (window.chartConfig) {
        if (window.chartConfig.minDistance !== undefined) {
            url.searchParams.set('min_distance', window.chartConfig.minDistance);
        }
        if (window.chartConfig.maxDistance !== undefined) {
            url.searchParams.set('max_distance', window.chartConfig.maxDistance);
        }
        if (window.chartConfig.loadedCount !== undefined) {
            url.searchParams.set('loaded_count', window.chartConfig.loadedCount);
        }
        if (window.chartConfig.seriescategories !== undefined) {
            url.searchParams.set('seriescategories', JSON.stringify(window.chartConfig.seriescategories));
        }
    }

    // Effectuer la requête GET
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
            window.chartConfig.stats = data.stats;
            if (data.stats) {
                updateStatistics(window.chartConfig.stats);
            }
            if (data.stats && data.categories) {
                generateStatsDivs(data.categories, data.stats);
            }

            window.chartConfig.loadedCount = data.loaded_count;
            window.chartConfig.totalCount = data.total_count;
        } else {
            document.getElementById('loaded-count').textContent = window.chartConfig.loadedCount;
            document.getElementById('total-count').textContent = window.chartConfig.totalCount;
        }
    })
    .catch(error => {
        console.error('Error during fetch:', error);
    })
    .finally(() => {
        window.isRefreshing = false;
    });
}






document.addEventListener('DOMContentLoaded', () => {
    console.log('Setting up periodic updates');
    console.log('info' + window.chartConfig.refreshInterval);

    updateCountdown({
        countdown: Math.floor(window.chartConfig.refreshInterval / 1000),
        message: "Prochaine mise à jour dans {seconds} secondes"
    }, document.getElementById('countdown'), fetchUpdates);
});
