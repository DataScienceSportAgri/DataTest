class GridOverlay {
    constructor(containerId = 'grid-container', displayWidth = 800) {
        console.log(`Initializing GridOverlay for container: ${containerId}`);
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container #${containerId} introuvable`);
        }
        console.log(`Container found:`, this.container);

        this.displayWidth = displayWidth;
        this.gridData = this.parseGridData();
        console.log('Parsed grid data:', this.gridData);

        this.initStructure();

        // Appeler les méthodes nécessaires pour afficher la grille
        this.calculateGridLayout();
        this.renderGrid();
    }

    initStructure() {
        console.log('Initializing grid structure...');
        const wrapper = document.createElement('div');
        wrapper.className = 'grid-wrapper';

        const gridElement = document.createElement('div');
        gridElement.className = 'grid-overlay';

        wrapper.appendChild(gridElement);
        this.container.appendChild(wrapper);

        // Associer l'élément DOM créé à l'attribut `this.grid`
        this.grid = gridElement;
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

    calculateGridLayout() {
        console.log('Calculating grid layout...');

        const containerWidth = parseInt(this.container.style.width || 0, 10);
        const containerHeight = parseInt(this.container.style.height || 0, 10);

        console.log(`Container dimensions: width=${containerWidth}, height=${containerHeight}`);

        if (!containerWidth || !containerHeight) {
            console.error('Container dimensions are not set correctly.');
            return;
        }

        const positions = {
            cols: new Set(),
            rows: new Set()
        };

        if (!this.gridData || !this.gridData.length) {
            console.error('No grid data available for layout calculation.');
            return;
        }

        this.gridData.forEach(({ coordinates }) => {
            positions.cols.add(coordinates[0]).add(coordinates[2]);
            positions.rows.add(coordinates[1]).add(coordinates[3]);
        });

        const sortedCols = Array.from(positions.cols).sort((a, b) => a - b);
        const sortedRows = Array.from(positions.rows).sort((a, b) => a - b);

        console.log('Sorted columns:', sortedCols);
        console.log('Sorted rows:', sortedRows);

        this.applyDynamicSizing(sortedCols, sortedRows, containerWidth, containerHeight);
        }

        applyDynamicSizing(cols, rows, totalWidth, totalHeight) {
        console.log('Applying dynamic sizing...');

        if (!cols.length || !rows.length) {
            console.error('Columns or rows are empty. Cannot apply dynamic sizing.');
            return;
        }

        const colSizes = cols.map((_, i) => (cols[i + 1] ? cols[i + 1] - cols[i] : totalWidth - cols[i]));
        const rowSizes = rows.map((_, i) => (rows[i + 1] ? rows[i + 1] - rows[i] : totalHeight - rows[i]));

        console.log('Column sizes:', colSizes);
        console.log('Row sizes:', rowSizes);

        this.grid.style.gridTemplateColumns = colSizes.map(size => `${size}px`).join(' ');
        this.grid.style.gridTemplateRows = rowSizes.map(size => `${size}px`).join(' ');
    }

    renderGrid() {
        console.log('Rendering grid...');

        if (!this.gridData || !this.gridData.length) {
            console.error('No grid data available for rendering.');
            return;
        }

        // Configuration de la grille CSS
        this.grid.style.display = 'grid';

        // Génération des cellules
        this.grid.innerHTML = '';

        const fragment = document.createDocumentFragment();

        this.gridData.forEach((zone, index) => {
            console.log(`Rendering cell ${index} with data:`, zone);

            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.gridArea = this.calculateGridPosition(zone.coordinates, index);
            cell.dataset.value = zone.mean_value.toFixed(4);

            // Style dynamique basé sur la valeur
            cell.style.backgroundColor = `rgba(0,100,200,${zone.mean_value * 2})`;
            cell.style.border = '1px solid rgba(255,255,255,0.3)';

            fragment.appendChild(cell);
        });

        this.grid.appendChild(fragment);
    }

    calculateGridPosition(coords) {
        if (!coords || coords.length !== 4) {
            console.error('Invalid coordinates for grid position calculation:', coords);
            return '';
        }

        const [x1, y1, x2, y2] = coords;

        // Correction des calculs pour éviter les erreurs
        return `${y1 + 1} / ${x1 + 1} / ${y2 + 1} / ${x2 + 1}`;
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

            const parsedData = JSON.parse(rawData);

            console.log('Parsed grid data successfully:', parsedData);

            return parsedData;

        } catch (error) {
            console.error('Error parsing grid data:', error);

        return [];
        }
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

    calculateGridLayout() {
        console.log('Calculating grid layout...');

        const containerWidth = parseInt(this.container.style.width || 0, 10);
        const containerHeight = parseInt(this.container.style.height || 0, 10);

        console.log(`Container dimensions: width=${containerWidth}, height=${containerHeight}`);

        if (!containerWidth || !containerHeight) {
            console.error('Container dimensions are not set correctly.');
            return;
        }

        const positions = {
            cols: new Set(),
            rows: new Set()
        };

        if (!this.gridData || !this.gridData.length) {
            console.error('No grid data available for layout calculation.');
            return;
        }

        this.gridData.forEach(({ coordinates }) => {
            positions.cols.add(coordinates[0]).add(coordinates[2]);
            positions.rows.add(coordinates[1]).add(coordinates[3]);
        });

        const sortedCols = Array.from(positions.cols).sort((a, b) => a - b);
        const sortedRows = Array.from(positions.rows).sort((a, b) => a - b);

        console.log('Sorted columns:', sortedCols);
        console.log('Sorted rows:', sortedRows);

        this.applyDynamicSizing(sortedCols, sortedRows, containerWidth, containerHeight);
    }

    applyDynamicSizing(cols, rows, totalWidth, totalHeight) {
        console.log('Applying dynamic sizing...');

        if (!cols.length || !rows.length) {
            console.error('Columns or rows are empty. Cannot apply dynamic sizing.');
            return;
        }

        const colSizes = cols.map((_, i) => (cols[i + 1] ? cols[i + 1] - cols[i] : totalWidth - cols[i]));
        const rowSizes = rows.map((_, i) => (rows[i + 1] ? rows[i + 1] - rows[i] : totalHeight - rows[i]));

        console.log('Column sizes:', colSizes);
        console.log('Row sizes:', rowSizes);

        this.grid.style.gridTemplateColumns = colSizes.map(size => `${size}px`).join(' ');
        this.grid.style.gridTemplateRows = rowSizes.map(size => `${size}px`).join(' ');
    }

    renderGrid() {
        console.log('Rendering grid...');

        if (!this.gridData || !this.gridData.length) {
            console.error('No grid data available for rendering.');
            return;
        }

        // Configuration de la grille CSS
        this.grid.style.display = 'grid';

        // Génération des cellules
        this.grid.innerHTML = '';

        const fragment = document.createDocumentFragment();

        this.gridData.forEach((zone, index) => {
            console.log(`Rendering cell ${index} with data:`, zone);

            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.gridArea = this.calculateGridPosition(zone.coordinates, index);
            cell.dataset.value = zone.mean_value.toFixed(4);

            // Style dynamique basé sur la valeur
            cell.style.backgroundColor = `rgba(0,100,200,${zone.mean_value * 2})`;
            cell.style.border = '1px solid rgba(255,255,255,0.3)';

            fragment.appendChild(cell);
        });

        this.grid.appendChild(fragment);
    }

    calculateGridPosition(coords) {
        if (!coords || coords.length !== 4) {
            console.error('Invalid coordinates for grid position calculation:', coords);
            return '';
        }

        const [x1, y1, x2, y2] = coords;

            // Correction des calculs pour éviter les erreurs
            return `${y1 + 1} / ${x1 + 1} / ${y2 + 1} / ${x2 + 1}`;
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

            const parsedData = JSON.parse(rawData);

            console.log('Parsed grid data successfully:', parsedData);

            return parsedData;

            } catch (error) {
                console.error('Error parsing grid data:', error);

            return [];
            }
        }
    }

    verifyGridZones({ renderedPixelRowSizes, renderedPixelColumnSizes }) {
        console.log('Verifying grid zones...');

        this.gridData.forEach(({ coordinates }, index) => {
            const [x1, y1, x2, y2] = coordinates.map(coord => coord * this.naturalToRendered);

            const matchingCells = Array.from(this.grid.children).filter(cell => {
                const colStart = parseInt(cell.dataset.colIndex) * renderedPixelColumnSizes[0];
                const rowStart = parseInt(cell.dataset.rowIndex) * renderedPixelRowSizes[0];
                return x1 >= colStart && x2 <= colStart + renderedPixelColumnSizes[0] &&
                       y1 >= rowStart && y2 <= rowStart + renderedPixelRowSizes[0];
            });

            if (matchingCells.length === 0) {
                console.error(`No matching cells found for zone ${index} with coordinates:`, coordinates);
            } else {
                console.log(`Zone ${index} verified successfully.`);
            }
        });
    }
}