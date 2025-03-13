import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';

// Define mock game state with player data
const mockGameState = {
  mapGrid: [[0, 0], [0, 0]],
  units: { 'A': { name: 'A', position: { x: 0, y: 0 }, player_id: 'p0' } },
  players: { 'p0': { id: 'p0', name: 'Player 1', color: '#F44336' } },
  coinPositions: [{ x: 1, y: 1 }],
  turn: 1
};

// Set up Jest mocks before imports
// Mock the API module
jest.mock('../api', () => ({
  getGameState: jest.fn().mockResolvedValue(mockGameState),
  getChatHistory: jest.fn().mockResolvedValue({ messages: [] }),
  sendChatMessage: jest.fn().mockResolvedValue(true),
  
  // Mock the gameClient object that App.tsx uses
  gameClient: {
    getCurrentGameState: jest.fn().mockReturnValue(mockGameState),
    getCurrentChatHistory: jest.fn().mockReturnValue({
      messages: []
    }),
    
    // Subscriptions with callbacks
    subscribeToGameState: jest.fn().mockImplementation(callback => {
      callback(mockGameState);
      return jest.fn(); // Return unsubscribe function
    }),
    
    subscribeToChatHistory: jest.fn().mockImplementation(callback => {
      callback({ messages: [] });
      return jest.fn();
    }),
    
    subscribeToConnectionState: jest.fn().mockImplementation(callback => {
      callback(true); // Simulate connected state
      return jest.fn();
    }),
    
    // Other methods
    isConnectionActive: jest.fn().mockReturnValue(true),
    connect: jest.fn(),
    requestGameState: jest.fn(),
    sendChatMessage: jest.fn().mockResolvedValue(true)
  }
}));

// Mock the ChatPanel component to avoid JSDOM issues with scrollIntoView
jest.mock('../components/ChatPanel', () => ({
  ChatPanel: ({ playerName, height }: { playerName?: string; height?: string | number }) => (
    <div data-testid="chat-panel" data-player-name={playerName} data-height={height}>
      Chat Panel Mock
    </div>
  )
}));

// Import after jest mocks are defined
import App from '../App';
import { getGameState, getChatHistory, sendChatMessage } from '../api';

// Create spies for tracking calls to the mocked functions
const getGameStateMock = getGameState as jest.Mock;
const getChatHistoryMock = getChatHistory as jest.Mock;
const sendChatMessageMock = sendChatMessage as jest.Mock;

describe('App', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    getGameStateMock.mockClear();
    getChatHistoryMock.mockClear();
    sendChatMessageMock.mockClear();
  });

  it('renders the app title', () => {
    render(<App />);
    const titleElement = screen.getByText(/GPT Generals/i);
    expect(titleElement).toBeInTheDocument();
  });

  it('displays the game state immediately with our mock', () => {
    render(<App />);
    const turnText = screen.getByText(/Turn: 1/i);
    expect(turnText).toBeInTheDocument();
  });

  it('displays turn number after loading', async () => {
    // Arrange the test
    render(<App />);
    
    // Act - wait for the async state update to complete using findByText
    // findByText internally uses waitFor which wraps updates in act()
    const turnText = await screen.findByText(/Turn: 1/i);
    
    // Assert
    expect(turnText).toBeInTheDocument();
  });
  
  it('includes the chat panel component', async () => {
    render(<App />);
    const chatPanel = await screen.findByTestId('chat-panel');
    expect(chatPanel).toBeInTheDocument();
  });
});
