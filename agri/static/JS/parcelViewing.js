
class ParcelViewer {
    constructor(containerId = 'grid-container') {
        // Définir les gestionnaires comme propriétés de classe
    this.globalHandler = (event) => {
        console.log('Global mouse movement:', event.clientX, event.clientY);
    };

    this.gridHandler = (event) => {
        console.log('Grid mouse movement:', event.clientX, event.clientY);
    };
       this.container = document.getElementById(containerId);
       this.displayWidth = 800;
       this.gridData = this.parseGridData();
       this.datePicker = document.getElementById('date-picker');
       this.currentDate = this.datePicker.value
       this.gridOverlay = null

    // Initialiser les éléments critiques
       this.setupEventListeners();
       this.image = document.getElementById('satellite-image');
       this.initCriticalElements();
       this.bandValues = document.getElementById('band-values-table');
        // Initialiser la grille après ajustement des dimensions

       this.initializeImage('grid-container', this.displayWidth, this.image);

    }

    initCriticalElements() {

        if (!this.container || !this.datePicker || !this.image) {
            console.error('Éléments manquants:', {
                container: !!this.container,
                datePicker: !!this.datePicker,
                image: !!this.image
            });
            throw new Error('Configuration invalide');
        }
    }


     initializeImage(container, display, img) {
        console.log('Initializing image...');

        // Configuration de base de l'image
        this.image.style.width = `${this.displayWidth}px`;
        this.image.style.height = 'auto';

        const initGrid = () => {
            const imageRatio = this.image.naturalHeight / this.image.naturalWidth;
            const displayHeight = this.displayWidth * imageRatio;

            // Ajuster les dimensions du conteneur
            this.container.style.height = `${displayHeight}px`;
            this.container.style.width = `${this.displayWidth}px`;
            this.container.style.position = 'relative';
            this.gridOverlay = new GridOverlay(container, display, img, this.gridData);

            console.log('parameters', this.gridOverlay.parameters)
            this.setupGridInteraction();
        };

        if (this.image.complete) {
            initGrid();
        } else {
            this.image.onload = initGrid;
        }
    }

    setupGridInteraction() {
        let lastHighlightedId = null;

        const throttledHandler = _.throttle((e) => {
            const rect = this.gridOverlay.grid.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            requestAnimationFrame(() => {
                const cell = document.elementFromPoint(e.clientX, e.clientY)?.closest('.grid-cell');

                if (cell && !this.gridOverlay.destroyed) {
                    const cellId = cell.dataset.backendId;
                    if (cellId !== lastHighlightedId) {
                        this.handleCellHover(cellId);
                        lastHighlightedId = cellId;
                    }
                } else {
                    this.resetHighlight();
                    this.resetBandValues(); // Ajout ici pour les sorties rapides
                    lastHighlightedId = null;
                }
            });
        }, 100);

        this.gridOverlay.grid.addEventListener('mousemove', throttledHandler);
        this.gridOverlay.grid.addEventListener('mouseleave', () => {
            this.resetHighlight();
            this.resetBandValues(); // Ajout principal ici
            lastHighlightedId = null;
        });

        this.cleanupGridInteractions = () => {
            this.gridOverlay.grid.removeEventListener('mousemove', throttledHandler);
            this.gridOverlay.grid.removeEventListener('mouseleave', this.resetHighlight);
        };
    }

    handleCellHover(cellId) {
        try {
            this.updateZoneData(cellId);
            // Appel direct à la méthode du GridOverlay
            this.gridOverlay.highlightCellById(cellId, 'rgba(255, 165, 0, 0.3)', 500);
        } catch (error) {
            console.error('Erreur hover:', error);
            this.resetHighlight();
        }
    }

    resetHighlight() {
        // Réinitialisation de toutes les cellules highlightées
        this.gridOverlay.grid.querySelectorAll('.grid-cell').forEach(cell => {
            this.gridOverlay.highlightCellById(cell.id, 'rgba(0, 100, 200, 0.1)', 0);
        });
    }


    setupEventListeners() {
        // Gestionnaire de changement de date
        this.datePicker.addEventListener('change', async (e) => {
            await this.handleDateChange(e.target.value);
            this.setupGridInteraction();
        });
    }

    get_variables_naturalPixelColumnSize({naturalPixelColumnSize}) {
        return naturalPixelColumnSize;
    }
    get_variables_naturalPixelRowSize({naturalPixelRowSize}) {
        return naturalPixelRowSize;
    }


    async handleDateChange(date) {
        this.naturalPixelRowSize =  this.get_variables_naturalPixelRowSize(this.gridOverlay.parameters)
        this.naturalPixelColumnSize = this.get_variables_naturalPixelColumnSize(this.gridOverlay.parameters)
        try {
            const response = await fetch('/agri/demo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: new URLSearchParams({
                    action: 'change_date',
                    date: date,
                    column_size: this.naturalPixelColumnSize,
                    row_size: this.naturalPixelRowSize
                })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                console.log('data grid',data.pixel_grid)
                // Mettre à jour l'image et réinitialiser la grille
                this.image.src = STATIC_URL + data.rgb_image_path;
                this.currentDate = date;
                this.gridData = this.updateGridData(data.pixel_grid)
                this.initializeImage('grid-container', this.displayWidth, this.image, this.gridData)
                this.resetBandValues();
                                // Deuxième requête à /agri/ndvi/
                const ndviResponse = await fetch(`/agri/ndvi/?date=${date}`, { // Utilisation de backticks
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!ndviResponse.ok) throw new Error(`HTTP error! status: ${ndviResponse.status}`);
                const ndviData = await ndviResponse.text(); // Supposons que la vue retourne du HTML

                const iframe = document.getElementById('ndvi_view'); // Assurez-vous que l'ID correspond à celui de votre iframe
                iframe.src = `/agri/ndvi/?date=${date}`; // Mettre à jour l'URL de l'iframe
                    } catch (error) {
                        console.error('Erreur lors du changement de date:', error);
                }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    async updateZoneData(cellId) {
        this.naturalPixelRowSize =  this.get_variables_naturalPixelRowSize(this.gridOverlay.parameters)
        this.naturalPixelColumnSize = this.get_variables_naturalPixelColumnSize(this.gridOverlay.parameters)
        try {
            const response = await fetch('/agri/demo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: new URLSearchParams({
                    action: 'get_zone_by_id',
                    cell_id: cellId,
                    date: this.currentDate,
                    column_size: this.naturalPixelColumnSize,
                    row_size: this.naturalPixelRowSize
                })
            });

            if (!response.ok) throw new Error(`Erreur HTTP! statut: ${response.status}`);

            const data = await response.json();
            console.log('data',data)
            this.displayBandValues(data);
        } catch (error) {
            console.error('Erreur lors de la récupération des données:', error);
            this.bandValues.innerHTML = `<div class="error">Erreur de chargement des données</div>`;
        }
    }


    parseGridData() {
        console.log('Parsing grid data...');

        const gridElement = document.querySelector('script[type="application/json"]#grid-data');

        if (!gridElement) {
            console.error('Element grid-data not found in the DOM.');
            return [];
        }

        try {
            const rawData = gridElement.textContent.trim();

            if (!rawData) {
            throw new Error('Grid data is empty.');
        }
        console.log('raw data', rawData)
        const parsedData = JSON.parse(rawData);

        console.log('Parsed grid data successfully:', parsedData);

        return parsedData;

        } catch (error) {
            console.error('Error parsing grid data:', error);

            return [];
        }
        const parsedData = JSON.parse(rawData);

        // Vérification supplémentaire recommandée
        const uniqueIds = new Set(parsedData.map(item => item.id));
        if (uniqueIds.size !== parsedData.length) {
            console.error('IDs dupliqués détectés !');
            return [];
        }
        console.log('parsed data',parsedData)
        return parsedData;
    }

    updateGridData (rawData) {
        const parsedData = JSON.parse(rawData);
        return parsedData
    }



    displayBandValues(data) {
        // Mise à jour des valeurs de bandes
        for (let bandNum = 1; bandNum <= 12; bandNum++) {
            const bandKey = `band_${bandNum}`;
            const value = data.bands[bandKey] ?? 'N/A';
            const elementId = `band-${bandNum}${bandNum === 8 ? 'a' : ''}-value`;
            document.getElementById(elementId).textContent = value;
        }
    }

    resetBandValues() {
        // Cibler uniquement les cellules de valeur dans le tableau spécifique
        const table = document.getElementById('band-values-table');
        const valueCells = table.querySelectorAll('tbody td[id^="band-"][id$="-value"]');

        // Réinitialisation sécurisée avec vérification d'existence
        if (valueCells.length > 0) {
            valueCells.forEach(cell => {
                cell.textContent = '-';
                cell.classList.remove('calculated-value'); // Supprime les classes liées au calcul
            });
        } else {
            console.warn('Aucune cellule de valeur trouvée dans le tableau');
        }
    }

}


class GridOverlay {
    constructor(containerId = 'grid-container', displayWidth = 800, imageElement, gridData = null) {
        this.image = imageElement; // Nouveau paramètre
        console.log(`Initializing GridOverlay for container: ${containerId}`);
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container #${containerId} introuvable`);
        }
        console.log(`Container found:`, this.container);

        this.displayWidth = displayWidth;
         // Récupération dynamique des données
        this.gridData = gridData || this.parseGridData()
        console.log('Parsed grid data:', this.gridData);
        this.grid = document.getElementById('gridContainer');
                console.log('Initializing grid structure...');

        // Créer le wrapper principal
        this.wrapper = document.createElement('div');
        this.wrapper.className = 'grid-wrapper';
        this.wrapper.style.position = 'absolute';
        this.wrapper.style.top = '0';
        this.wrapper.style.left = '0';
        this.wrapper.style.width = '100%';
        this.wrapper.style.height = '100%';

        // Créer l'élément de grille
        this.grid = document.createElement('div');
        this.grid.className = 'grid-overlay';
        this.grid.style.display = 'grid';
        this.grid.style.position = 'absolute';
        this.grid.style.width = '100%';
        this.grid.style.height = '100%';

        // Ajouter la grille au wrapper
        this.wrapper.appendChild(this.grid);

        // Ajouter le wrapper au conteneur principal
        this.container.appendChild(this.wrapper);

        this.parameters = this.calculateGridParameters();
        const params = this.parameters
        this.initStructure(params);
    }

    initStructure(params) {

        this.createGrid(params);
        this.verifyGridZones(params);
        console.log('Grid structure initialized:', this.grid);
    }

    async loadImage(imageUrl) {
        console.log(`Loading image from URL: ${imageUrl}`);
        await new Promise((resolve) => {
            this.image = new Image();
            this.image.src = imageUrl;
            this.image.onload = () => {
                console.log('Image loaded successfully:', this.image);
                resolve();
            };
            this.image.onerror = (err) => {
                console.error('Error loading image:', err);
            };
        });

        this.calculateGridLayout();
    }


    calculateGridParameters() {

        console.log('Calculating grid parameters...');

        if (!this.gridData || this.gridData.length === 0) {
            throw new Error('Grid data is empty or invalid.');
        }

        //Récupérer les coordonnées du premier élément
        const firstCoordinates = this.gridData[0].coordinates;
        const [x1, y1, x2, y2] = firstCoordinates;

        // Calculer les tailles naturelles des pixels
        const naturalPixelRowSize = y2 - y1; // Différence entre les positions impaires
        const naturalPixelColumnSize = x2 - x1; // Différence entre les positions paires

        if (!Number.isInteger(naturalPixelRowSize) || !Number.isInteger(naturalPixelColumnSize)) {
            throw new Error('Natural pixel sizes must be integers.');
        }

        console.log(`Natural Pixel Row Size: ${naturalPixelRowSize}, Natural Pixel Column Size: ${naturalPixelColumnSize}`);

        // Calculer le nombre de lignes et de colonnes
        const allOddPositions = this.gridData.flatMap(({ coordinates }) => [coordinates[1], coordinates[3]]);
        const allEvenPositions = this.gridData.flatMap(({ coordinates }) => [coordinates[0], coordinates[2]]);

        const minOdd = Math.min(...allOddPositions);
        const maxOdd = Math.max(...allOddPositions);
        const minEven = Math.min(...allEvenPositions);
        const maxEven = Math.max(...allEvenPositions);

        const numberOfRows = Math.ceil((maxOdd - minOdd) / naturalPixelRowSize);
        const numberOfColumns = Math.ceil((maxEven - minEven) / naturalPixelColumnSize);

        if (!Number.isInteger(numberOfRows) || !Number.isInteger(numberOfColumns)) {
            throw new Error('Number of rows and columns must be integers.');
        }

        console.log(`Number of Rows: ${numberOfRows}, Number of Columns: ${numberOfColumns}`);

        // Calculer le ratio de conversion naturel -> rendu
        const naturalToRendered = this.displayWidth / this.image.naturalWidth;

        // Calculer les tailles rendues des pixels
        let renderedPixelRowSize = naturalPixelRowSize * naturalToRendered;
        let renderedPixelColumnSize = naturalPixelColumnSize * naturalToRendered;

        console.log(`Rendered Pixel Row Size: ${renderedPixelRowSize}, Rendered Pixel Column Size: ${renderedPixelColumnSize}`);
        console.log(`Total height Size: ${this.container.offsetHeight}, Total width size: ${this.container.offsetWidth}`)
        // Ajustement pour garantir que la somme des tailles rendues correspond à la taille totale
        renderedPixelRowSize = this.adjustSizes(renderedPixelRowSize, numberOfRows, this.container.offsetHeight);
        renderedPixelColumnSize = this.adjustSizes(renderedPixelColumnSize, numberOfColumns, this.container.offsetWidth);

        return {
            naturalPixelRowSize,
            naturalPixelColumnSize,
            numberOfRows,
            numberOfColumns,
            renderedPixelRowSizes: renderedPixelRowSize,
            renderedPixelColumnSizes: renderedPixelColumnSize,
            naturalToRendered
        };
    }

    adjustSizes(baseSize, count, totalPixels) {
        console.log(`Adjusting sizes for base size: ${baseSize}, count: ${count}, total pixels: ${totalPixels}`);

        const baseSizeFloor = Math.floor(baseSize);
        const fractionalPart = baseSize - baseSizeFloor;
        let largerElementsCount = Math.round(count * fractionalPart);

        // Création du tableau initial
        let sizes = Array(count).fill(baseSizeFloor);
        for (let i = 0; i < largerElementsCount; i++) {
            sizes[i] += 1;
        }

        // Calcul du total
        let currentTotal = sizes.reduce((sum, size) => sum + size, 0);
        const difference = totalPixels - currentTotal;

        // Ajustement aléatoire amélioré
        if (difference !== 0) {
            const avg = totalPixels / count;
            let eligibleIndices = [];

            if (difference > 0) {
                eligibleIndices = sizes
                    .map((size, index) => size < avg ? index : -1)
                    .filter(index => index !== -1);
            } else {
                eligibleIndices = sizes
                    .map((size, index) => size > avg ? index : -1)
                    .filter(index => index !== -1);
            }

            // Sélection aléatoire
            const indexToAdjust = eligibleIndices.length > 0
                ? eligibleIndices[Math.floor(Math.random() * eligibleIndices.length)]
                : Math.floor(Math.random() * count);

            sizes[indexToAdjust] += difference;
        }

        console.log(`Adjusted sizes:`, sizes);
        return sizes;
    }

    createGrid({ renderedPixelRowSizes, renderedPixelColumnSizes, gridData }) {
        console.log('Creating grid with calculated dimensions...');

        // Appliquer les tailles calculées
        this.grid.style.gridTemplateRows = renderedPixelRowSizes.map(size => `${size}px`).join(' ');
        this.grid.style.gridTemplateColumns = renderedPixelColumnSizes.map(size => `${size}px`).join(' ');

        // Calculer les totaux avec marge de tolérance
        const totalRenderedWidth = renderedPixelColumnSizes.reduce((a, b) => a + b, 0);
        const totalRenderedHeight = renderedPixelRowSizes.reduce((a, b) => a + b, 0);
        const expectedWidth = this.displayWidth;
        const expectedHeight = Math.round(this.displayWidth * (this.image.naturalHeight / this.image.naturalWidth));

        // Vérification avec marge de 2 pixels
        const widthMismatch = Math.abs(totalRenderedWidth - expectedWidth) > 2;
        const heightMismatch = Math.abs(totalRenderedHeight - expectedHeight) > 2;

        if (widthMismatch || heightMismatch) {
            console.error(`Écart trop important:
                Largeur: ${totalRenderedWidth} vs ${expectedWidth}
                Hauteur: ${totalRenderedHeight} vs ${expectedHeight}`);
            return;
        }
            // Validation renforcée
        if (!Array.isArray(this.gridData)) {
            console.error('gridData doit être un tableau', gridData);
            gridData = [];
        }


            // Création des cellules dans l'ordre strict du gridData
        this.grid.innerHTML = '';
        this.gridData.forEach((cellData, index) => {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';

            // Calcul des indices à partir de la position dans gridData
            const numColumns = renderedPixelColumnSizes.length;
            const rowIndex = Math.floor(index / numColumns);
            const colIndex = index % numColumns;

            // Assignation des propriétés
            cell.id = cellData.id;
            cell.dataset.backendId = cellData.id;
            cell.dataset.rowIndex = rowIndex;
            cell.dataset.colIndex = colIndex;

            Object.assign(cell.style, {
                border: '1px solid rgba(255,255,255,0.3)',
                backgroundColor: 'rgba(0, 100, 200, 0.1)',
                boxSizing: 'border-box'
            });

            this.grid.appendChild(cell);
        });
    }

    verifyGridZones({ renderedPixelRowSizes, renderedPixelColumnSizes, naturalToRendered, gridData }) {
        console.log('Vérification des zones par ID...');

        // Créer une map des cellules frontend par ID
        const cellMap = new Map();
        Array.from(this.grid.children).forEach(cell => {
            cellMap.set(cell.id, {
                element: cell,
                row: parseInt(cell.dataset.rowIndex),
                col: parseInt(cell.dataset.colIndex)
            });
        });
        // Validation critique
        if (typeof naturalToRendered !== 'number' || isNaN(naturalToRendered)) {
            console.error('naturalToRendered invalide:', naturalToRendered);
            return;
        }


        this.gridData.forEach((zone, index) => {
            console.log('verification de zone',zone.coordinates)
            // Conversion explicite en nombres
            const [x1, y1, x2, y2] = zone.coordinates.map(coord => {
                const num = Number(coord);
                return isNaN(num) ? 0 : num * naturalToRendered;
            });
            console.log('verification des variables',x1, y1, x2, y2)
            const zoneId = zone.id;

            // Récupérer la cellule correspondante
            const cellData = cellMap.get(zoneId);

            if (!cellData) {
                console.error(`Zone ${index} (ID: ${zoneId}) : Aucune cellule correspondante`);
                return;
            }

            // Calculer les positions théoriques
            const colPos = this.calculateCumulativePositions(renderedPixelColumnSizes);
            const rowPos = this.calculateCumulativePositions(renderedPixelRowSizes);

            const expectedX1 = colPos[cellData.col];
            const expectedX2 = colPos[cellData.col + 1];
            const expectedY1 = rowPos[cellData.row];
            const expectedY2 = rowPos[cellData.row + 1];

            // Vérifier la correspondance spatiale
            const positionMatch = this.overlapCheck(x1, x2, expectedX1, expectedX2) &&
                                 this.overlapCheck(y1, y2, expectedY1, expectedY2);

            if (!positionMatch) {
                console.error(`Zone ${zoneId} : Incohérence positionnelle\n`,
                            `Backend: [${x1},${y1}]→[${x2},${y2}]\n`,
                            `Frontend: [${expectedX1},${expectedY1}]→[${expectedX2},${expectedY2}]`);
            }
            console.log('cell data element', cellData.element)
            // Vérification visuelle
            this.highlightMatchingCells(cellData.element, positionMatch);
        });
    }


    overlapCheck(a1, a2, b1, b2) {
        const TOLERANCE_PIXELS = 3; // Nouvelle tolérance de 3 pixels
        return (a1 - TOLERANCE_PIXELS) < (b2 + TOLERANCE_PIXELS) &&
               (a2 + TOLERANCE_PIXELS) > (b1 - TOLERANCE_PIXELS);
    }

    // Méthode de débogage visuel améliorée
    highlightMatchingCells(cells, positionMatch) {
        const elements = Array.isArray(cells) ? cells : [cells];
        const hue = (Math.random() * 360);

        // Fonction de conversion HSL vers nom approximatif
        const getColorName = (h) => {
            const colors = {
                0: 'Rouge', 15: 'Orange', 45: 'Jaune',
                70: 'Vert clair', 160: 'Vert', 180: 'Cyan',
                240: 'Bleu', 270: 'Bleu roi', 300: 'Violet',
                330: 'Magenta', 360: 'Rouge'
            };
            const thresholds = Object.keys(colors).map(Number).sort((a,b) => a-b);
            for (let i = 0; i < thresholds.length; i++) {
                if (h <= thresholds[i]) return colors[thresholds[i]];
            }
            return 'Inconnu';
        };

        const colorCode = `hsl(${Math.round(hue)}, 70%, 50%)`;
        const colorName = getColorName(hue);

        elements.forEach(element => {
            if (!element?.id) return;

            element.style.transition = 'background-color 0.3s';
            element.style.backgroundColor = colorCode;

            // Log détaillé
            console.log(
                `Cellule ${element.id}\n` +
                `Couleur: ${colorCode} (${colorName})\n` +
                `Position: row=${element.dataset.rowIndex} col=${element.dataset.colIndex}\n` +
                `Élément:`, element
            );
        });

        setTimeout(() => {
            elements.forEach(element => {
                if (element.style) element.style.backgroundColor = '';
            });
        }, 2000);
    }

    calculateCumulativePositions(sizes) {
        // Validation de l'entrée
        if (!Array.isArray(sizes)) {
            console.error("Erreur: 'sizes' doit être un tableau", sizes);
            return [0]; // Retourne une position minimale sécurisée
        }

        const positions = [0];
        for (let i = 0; i < sizes.length; i++) {
            // Validation des valeurs numériques
            if (typeof sizes[i] !== 'number' || isNaN(sizes[i])) {
                console.warn(`Valeur invalide à l'index ${i}:`, sizes[i]);
                sizes[i] = 0; // Corrige avec une valeur par défaut
            }

            positions.push(positions[i] + sizes[i]);
        }
        return positions;
    }

    highlightCellById(id, color = 'rgba(255, 0, 0, 0.3)', duration = 2000) {
        const cell = document.getElementById(id);
        if (!cell) {
            console.error(`Cellule avec l'ID ${id} introuvable`);
            return;
        }

        // Sauvegarde la couleur originale
        const originalColor = cell.style.backgroundColor;

        // Applique la nouvelle couleur
        cell.style.backgroundColor = color;
        console.log(`Cellule ${id} highlightée en ${color}`);

        // Réinitialisation après la durée spécifiée
        if (duration > 0) {
            setTimeout(() => {
                cell.style.backgroundColor = originalColor;
                console.log(`Réinitialisation de la couleur pour ${id}`);
            }, duration);
        }
    }

}




function checkLodash() {
    if (typeof _ === 'undefined') {
        console.error('Lodash not loaded');
        return false;
    }
    return true;
}

// Initialisation seulement si Lodash est chargé
document.addEventListener('DOMContentLoaded', () => {
    if (checkLodash()) {
        new ParcelViewer('grid-container');
    }
});