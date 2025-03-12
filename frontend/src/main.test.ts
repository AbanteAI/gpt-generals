import { Game } from './main';
import { Renderer } from './renderer';
import { Api } from './api';

// Mock the dependencies
jest.mock('./renderer');
jest.mock('./api');

describe('Game', () => {
  // Mock the DOM
  beforeEach(() => {
    // Create a mock container element
    document.body.innerHTML = '<div id="app"></div>';
    
    // Clear mock calls
    jest.clearAllMocks();
    
    // Mock the interval
    jest.useFakeTimers();
    
    // Mock setInterval and clearInterval
    jest.spyOn(window, 'setInterval');
    jest.spyOn(window, 'clearInterval');
  });
  
  afterEach(() => {
    // Restore original timer functions
    jest.useRealTimers();
    jest.restoreAllMocks();
  });
  
  test('constructor initializes renderer correctly', () => {
    // Mock the Renderer constructor to verify it's called
    const MockRenderer = Renderer as jest.MockedClass<typeof Renderer>;
    
    // Create game instance
    const game = new Game();
    
    // Check that renderer was initialized with the correct container ID
    expect(MockRenderer).toHaveBeenCalledWith('app');
  });
  
  test('start calls updateGameState and sets interval', async () => {
    // Mock the Api.getGameState method
    const mockGameState = { 
      mapGrid: [], 
      units: {}, 
      coinPositions: [], 
      turn: 0 
    };
    const mockGetGameState = jest.fn().mockResolvedValue(mockGameState);
    (Api.getGameState as jest.Mock) = mockGetGameState;
    
    // Create game instance with mocked services
    const game = new Game();
    
    // Ensure initial call is made
    expect(mockGetGameState).toHaveBeenCalledTimes(1);
    
    // Reset mock to isolate the next call
    mockGetGameState.mockClear();
    
    // Advance timers to trigger interval
    jest.runOnlyPendingTimers();
    
    // Wait for the async task to complete
    await Promise.resolve();
    
    // Should have called getGameState again
    expect(mockGetGameState).toHaveBeenCalledTimes(1);
    
    // Verify setInterval was called with correct interval
    expect(window.setInterval).toHaveBeenCalledWith(expect.any(Function), 1000);
  });
  
  test('stop clears the update interval', () => {
    // Setup with a non-null interval
    const game = new Game();
    
    // Ensure we have a valid interval ID
    const intervalId = 123;
    // @ts-ignore - access private property for testing
    game['updateInterval'] = intervalId;
    
    // Call stop method
    game.stop();
    
    // Check that clearInterval was called with the correct ID
    expect(window.clearInterval).toHaveBeenCalledWith(intervalId);
  });
});
