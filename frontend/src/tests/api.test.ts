import { getGameState } from '../api';
import { TerrainType } from '../models';

describe('API functions', () => {
  test('getGameState returns valid game state', async () => {
    const gameState = await getGameState();
    
    // Check that the game state has all required fields
    expect(gameState).toHaveProperty('mapGrid');
    expect(gameState).toHaveProperty('units');
    expect(gameState).toHaveProperty('coinPositions');
    expect(gameState).toHaveProperty('turn');
    
    // Check that the map grid is 10x10
    expect(gameState.mapGrid.length).toBe(10);
    expect(gameState.mapGrid[0].length).toBe(10);
    
    // Check that each map cell is either LAND or WATER
    for (const row of gameState.mapGrid) {
      for (const cell of row) {
        expect([TerrainType.LAND, TerrainType.WATER]).toContain(cell);
      }
    }
    
    // Check that units exist
    expect(Object.keys(gameState.units).length).toBeGreaterThan(0);
    expect(gameState.units).toHaveProperty('A');
    expect(gameState.units).toHaveProperty('B');
    
    // Check that coins exist
    expect(gameState.coinPositions.length).toBeGreaterThan(0);
    
    // Check that turn is a number
    expect(typeof gameState.turn).toBe('number');
  });
});
