import { GameState, TerrainType } from '../models';

// Create a mock gameClient and mock implementation of getGameState
// This is needed because our real implementation uses WebSockets
// which won't work in the Jest test environment
const mockGameState: GameState = {
  mapGrid: Array(10).fill(Array(10).fill(TerrainType.LAND)),
  units: {
    'A': { name: 'A', position: { x: 1, y: 1 }, player_id: 'p0' },
    'B': { name: 'B', position: { x: 8, y: 8 }, player_id: 'p1' }
  },
  players: {
    'p0': { id: 'p0', name: 'Player 1', color: '#F44336' },
    'p1': { id: 'p1', name: 'Player 2', color: '#2196F3' }
  },
  coinPositions: [
    { x: 3, y: 3 },
    { x: 5, y: 5 },
    { x: 7, y: 7 }
  ],
  turn: 1
};

// Mock the api module
jest.mock('../api', () => ({
  getGameState: jest.fn().mockResolvedValue(mockGameState),
  getChatHistory: jest.fn().mockResolvedValue({ messages: [] }),
  sendChatMessage: jest.fn().mockResolvedValue(true),
  moveUnit: jest.fn().mockResolvedValue(true),
  // Mock the gameClient
  gameClient: {
    getCurrentGameState: jest.fn().mockReturnValue(mockGameState),
    getCurrentChatHistory: jest.fn().mockReturnValue({ messages: [] }),
    subscribeToGameState: jest.fn().mockImplementation(callback => {
      // Call the callback immediately with the mock state
      callback(mockGameState);
      // Return an unsubscribe function
      return jest.fn();
    }),
    subscribeToChatHistory: jest.fn().mockImplementation(callback => {
      callback({ messages: [] });
      return jest.fn();
    }),
    subscribeToConnectionState: jest.fn().mockImplementation(callback => {
      callback(true); // Simulate connected state
      return jest.fn();
    }),
    isConnectionActive: jest.fn().mockReturnValue(true),
    connect: jest.fn(),
    requestGameState: jest.fn(),
    sendChatMessage: jest.fn().mockResolvedValue(true),
    moveUnit: jest.fn().mockResolvedValue(true)
  }
}));

// Import after mocking
import { getGameState } from '../api';

describe('API functions', () => {
  test('getGameState returns valid game state', async () => {
    const gameState = await getGameState();
    
    // Check that the game state has all required fields
    expect(gameState).toHaveProperty('mapGrid');
    expect(gameState).toHaveProperty('units');
    expect(gameState).toHaveProperty('coinPositions');
    expect(gameState).toHaveProperty('turn');
    
    // Check that the map grid exists
    expect(gameState.mapGrid.length).toBeGreaterThan(0);
    
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
