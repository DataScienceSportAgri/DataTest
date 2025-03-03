

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
        Plotly.react('chart-container', newData.data, newData.layout);
    } else {
        console.error("Plotly n'est pas chargé correctement");
    }
}

function postUpdates() {
window.isRefreshing = true;

  // Récupérer le jeton CSRF
  let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  if (!csrftoken) {
    csrftoken = getCookie('csrf_token');
  }

  if (!csrftoken) {
    console.error('CSRF token not found. Request may fail.');
  }


  var selectedCourseTypes = Array.isArray(chartConfig.typeList)
      ? window.chartConfig.typeList
      : [window.chartConfig.typeList];

  // Préparer les données à envoyer
  const data = {
    action: 'update',
    seriesCategories: chartConfig.seriesCategories || {},
    minDistance: chartConfig.minDistance,
    maxDistance: chartConfig.maxDistance,
    course_types: chartConfig.typeList,
    loaded_count: chartConfig.loadedCount
  };

  // Convertir l'objet en chaîne JSON
  const jsonData = JSON.stringify(data);

  // Effectuer la requête POST
  return fetch('/graph/vitesse-distribution/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: jsonData
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erreur réseau');
    }
    return response.json();
  })
  .then(data => {

    // Mettre à jour le graphique
    updateGraph(data.plot_data);

    // Mettre à jour les compteurs et les statistiques
    if (data.is_update) {
      document.getElementById('loaded-count').textContent = data.loaded_count;
      document.getElementById('total-count').textContent = data.total_count;
      window.chartConfig.stats = data.stats;
      if (data.stats) {
        updateStatistics(window.chartConfig.stats);
      }
      if (data.stats && data.categories_selected) {
        generateStatsDivs(data.stats);
      }

      window.chartConfig.loadedCount = data.loaded_count;
      window.chartConfig.totalCount = data.total_count;
    } else {
      document.getElementById('loaded-count').textContent = window.chartConfig.loadedCount;
      document.getElementById('total-count').textContent = window.chartConfig.totalCount;
    }

    return data;
  })
  .catch(error => {
    console.error('Erreur:', error);
    throw error;
  })
  .finally(() => {
    window.isRefreshing = false;
  });
}







document.addEventListener('DOMContentLoaded', () => {
    console.log('Setting up periodic updates');

    updateCountdown({
        countdown: Math.floor(window.chartConfig.refreshInterval / 1000),
        message: "Prochaine mise à jour dans {seconds} secondes"
    }, document.getElementById('countdown'), postUpdates);
});
