// buttons.js
import { D3Chart } from './d3-chart.js';

export class ChartControls {
  constructor(chartContainerSelector) {
    this.chart = new D3Chart(chartContainerSelector);
    this.initEventListeners();
  }

  initEventListeners() {
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
      radio.addEventListener('change', () => this.handleControlChange());
    });
  }

  async handleControlChange() {
    try {
      const params = this.getCurrentParams();
      const newData = await this.fetchData(params);
      this.chart.update(newData);
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      this.showError('Une erreur est survenue lors de la mise à jour du graphique');
    }
  }

  getCurrentParams() {
    return {
      scoreType: document.querySelector('input[name="scoreType"]:checked').value,
      performanceTier: document.querySelector('input[name="performanceTier"]:checked').value,
      cohortType: document.querySelector('input[name="cohortType"]:checked').value
    };
  }

  async fetchData(params) {
    const response = await fetch('/graph/score-distribution/?' + new URLSearchParams(params), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    return response.json();
  }

  showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
  }
}
