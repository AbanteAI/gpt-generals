import { GameState, TerrainType, Position } from './models';

export class Renderer {
  private canvasElement: HTMLElement;
  private tileSize: number = 30; // Size of each tile in pixels
  
  constructor(containerId: string) {
    const container = document.getElementById(containerId);
    if (!container) {
      throw new Error(`Container element with id '${containerId}' not found`);
    }
    
    this.canvasElement = document.createElement('div');
    this.canvasElement.className = 'game-canvas';
    container.appendChild(this.canvasElement);
  }
  
  render(gameState: GameState): void {
    this.canvasElement.innerHTML = ''; // Clear the canvas
    
    const { mapGrid, units, coinPositions } = gameState;
    
    // Create a grid container
    const gridContainer = document.createElement('div');
    gridContainer.className = 'grid-container';
    gridContainer.style.gridTemplateColumns = `repeat(${mapGrid[0].length}, ${this.tileSize}px)`;
    gridContainer.style.gridTemplateRows = `repeat(${mapGrid.length}, ${this.tileSize}px)`;
    
    // Add tiles to the grid
    for (let y = 0; y < mapGrid.length; y++) {
      for (let x = 0; x < mapGrid[y].length; x++) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        
        // Set the base terrain type
        const terrainType = mapGrid[y][x];
        tile.classList.add(terrainType === TerrainType.LAND ? 'land' : 'water');
        
        // Check if there's a unit at this position
        let unitAtPosition = null;
        for (const unitKey in units) {
          const unit = units[unitKey];
          if (unit.position.x === x && unit.position.y === y) {
            unitAtPosition = unit;
            break;
          }
        }
        
        // Check if there's a coin at this position
        const coinAtPosition = coinPositions.some(pos => pos.x === x && pos.y === y);
        
        // Add content to the tile based on what's there
        if (unitAtPosition) {
          tile.classList.add('unit');
          tile.textContent = unitAtPosition.name;
        } else if (coinAtPosition) {
          tile.classList.add('coin');
          tile.textContent = 'c';
        }
        
        gridContainer.appendChild(tile);
      }
    }
    
    // Add turn information
    const turnInfo = document.createElement('div');
    turnInfo.className = 'turn-info';
    turnInfo.textContent = `Turn: ${gameState.turn}`;
    
    this.canvasElement.appendChild(gridContainer);
    this.canvasElement.appendChild(turnInfo);
  }
}
