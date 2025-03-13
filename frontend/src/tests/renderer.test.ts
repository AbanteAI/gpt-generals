import { Renderer } from '../renderer';
import { GameState, TerrainType } from '../models';

describe('Renderer', () => {
  // Mock DOM elements
  beforeEach(() => {
    // Create a mock container element
    document.body.innerHTML = '<div id="test-container"></div>';
  });
  
  test('constructor creates canvas element', () => {
    const renderer = new Renderer('test-container');
    const container = document.getElementById('test-container');
    
    // Check that the canvas element was added to the container
    const canvasElement = container?.querySelector('.game-canvas');
    expect(canvasElement).not.toBeNull();
  });
  
  test('render creates grid with correct number of tiles', () => {
    const renderer = new Renderer('test-container');
    
    // Create a simple game state with a 3x3 grid
    const gameState: GameState = {
      mapGrid: [
        [TerrainType.LAND, TerrainType.WATER, TerrainType.LAND],
        [TerrainType.WATER, TerrainType.LAND, TerrainType.WATER],
        [TerrainType.LAND, TerrainType.WATER, TerrainType.LAND]
      ],
      units: {
        'A': { name: 'A', position: { x: 0, y: 0 } }
      },
      coinPositions: [
        { x: 2, y: 2 }
      ],
      turn: 1
    };
    
    renderer.render(gameState);
    
    // Get the grid container
    const gridContainer = document.querySelector('.grid-container');
    expect(gridContainer).not.toBeNull();
    
    // Check that the grid has the correct number of tiles (3x3 = 9)
    const tiles = document.querySelectorAll('.tile');
    expect(tiles.length).toBe(9);
    
    // Check that there's one unit tile
    const unitTiles = document.querySelectorAll('.tile.unit');
    expect(unitTiles.length).toBe(1);
    
    // Check that there's one coin tile
    const coinTiles = document.querySelectorAll('.tile.coin');
    expect(coinTiles.length).toBe(1);
    
    // Check that there's a turn info element
    const turnInfo = document.querySelector('.turn-info');
    expect(turnInfo).not.toBeNull();
    expect(turnInfo?.textContent).toBe('Turn: 1');
  });
});
