/**
 * @jest-environment jsdom
 */
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
    
    // Mock the interval functions
    jest.useFakeTimers();
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
});
