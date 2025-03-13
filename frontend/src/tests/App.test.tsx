import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import App from '../App';

// Mock the API call
const mockGameState = {
  mapGrid: [[0, 0], [0, 0]],
  units: { 'A': { name: 'A', position: { x: 0, y: 0 } } },
  coinPositions: [{ x: 1, y: 1 }],
  turn: 1
};

const mockChatHistory = {
  messages: []
};

const getGameStateMock = jest.fn().mockResolvedValue(mockGameState);
const getChatHistoryMock = jest.fn().mockResolvedValue(mockChatHistory);
const sendChatMessageMock = jest.fn().mockResolvedValue(true);

// Mock the ChatPanel component to avoid JSDOM issues with scrollIntoView
jest.mock('../components/ChatPanel', () => ({
  ChatPanel: ({ playerName, height }: { playerName?: string; height?: string | number }) => (
    <div data-testid="chat-panel" data-player-name={playerName} data-height={height}>
      Chat Panel Mock
    </div>
  )
}));

// Create mock implementations for the API module 
// Note: This must come BEFORE the jest.mock call
const createApiMock = () => {
  return {
    getGameState: () => getGameStateMock(),
    getChatHistory: () => getChatHistoryMock(),
    sendChatMessage: (
      sender: string, 
      content: string, 
      senderType: 'player' | 'system' | 'unit'
    ) => sendChatMessageMock(sender, content, senderType),
    
    // Mock the gameClient object that App.tsx uses
    gameClient: {
      getCurrentGameState: jest.fn().mockReturnValue({
        mapGrid: [[0, 0], [0, 0]],
        units: { 'A': { name: 'A', position: { x: 0, y: 0 } } },
        coinPositions: [{ x: 1, y: 1 }],
        turn: 1
      }),
      getCurrentChatHistory: jest.fn().mockReturnValue({
        messages: []
      }),
      
      // Subscriptions with callbacks
      subscribeToGameState: jest.fn().mockImplementation(callback => {
        callback({
          mapGrid: [[0, 0], [0, 0]],
          units: { 'A': { name: 'A', position: { x: 0, y: 0 } } },
          coinPositions: [{ x: 1, y: 1 }],
          turn: 1
        });
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
  };
};

// Mock the API functions
jest.mock('../api', () => createApiMock());

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

  it('shows loading state initially', () => {
    render(<App />);
    const loadingElement = screen.getByText(/Loading game state/i);
    expect(loadingElement).toBeInTheDocument();
  });

  it('displays turn number after loading', async () => {
    // Arrange the test
    render(<App />);
    
    // Act - wait for the async state update to complete using findByText
    // findByText internally uses waitFor which wraps updates in act()
    const turnText = await screen.findByText(/Turn: 1/i);
    
    // Assert
    expect(turnText).toBeInTheDocument();
    
    // Verify mock was called
    await waitFor(() => {
      expect(getGameStateMock).toHaveBeenCalled();
    });
  });
  
  it('includes the chat panel component', async () => {
    render(<App />);
    const chatPanel = await screen.findByTestId('chat-panel');
    expect(chatPanel).toBeInTheDocument();
  });
});
