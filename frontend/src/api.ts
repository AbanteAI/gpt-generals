import { GameState, TerrainType, Position } from './models';

export class Api {
  // Mock function to get game state
  static async getGameState(): Promise<GameState> {
    // Generate a mock game state
    const width = 10;
    const height = 10;
    
    // Create a random map with land and water
    const mapGrid: TerrainType[][] = [];
    for (let y = 0; y < height; y++) {
      const row: TerrainType[] = [];
      for (let x = 0; x < width; x++) {
        // 20% chance of water
        row.push(Math.random() < 0.2 ? TerrainType.WATER : TerrainType.LAND);
      }
      mapGrid.push(row);
    }
    
    // Create mock units
    const units: Record<string, Unit> = {
      'A': { name: 'A', position: { x: 1, y: 1 } },
      'B': { name: 'B', position: { x: 8, y: 8 } }
    };
    
    // Create mock coins
    const coinPositions: Position[] = [
      { x: 3, y: 3 },
      { x: 5, y: 7 },
      { x: 7, y: 2 }
    ];
    
    // Create mock game state
    const gameState: GameState = {
      mapGrid,
      units,
      coinPositions,
      turn: Math.floor(Math.random() * 10) // Random turn number
    };
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 100));
    
    return gameState;
  }
}
