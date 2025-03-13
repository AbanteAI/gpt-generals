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

const getGameStateMock = jest.fn().mockResolvedValue(mockGameState);

jest.mock('../api', () => ({
  getGameState: () => getGameStateMock()
}));

describe('App', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    getGameStateMock.mockClear();
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
});
