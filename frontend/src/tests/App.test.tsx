import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock the API call
jest.mock('../api', () => ({
  getGameState: jest.fn().mockResolvedValue({
    mapGrid: [[0, 0], [0, 0]],
    units: { 'A': { name: 'A', position: { x: 0, y: 0 } } },
    coinPositions: [{ x: 1, y: 1 }],
    turn: 1
  })
}));

describe('App', () => {
  it('renders the app title', async () => {
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
    render(<App />);
    const turnText = await screen.findByText(/Turn: 1/i);
    expect(turnText).toBeInTheDocument();
  });
});
