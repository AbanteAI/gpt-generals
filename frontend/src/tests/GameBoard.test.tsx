import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { GameBoard } from '../components/GameBoard';
import { TerrainType } from '../models';

describe('GameBoard', () => {
  const mockGameState = {
    mapGrid: [
      [TerrainType.LAND, TerrainType.WATER],
      [TerrainType.WATER, TerrainType.LAND]
    ],
    units: {
      'A': { name: 'A', position: { x: 0, y: 0 }, player_id: 'p0' }
    },
    players: {
      'p0': { id: 'p0', name: 'Player 1', color: '#F44336' }
    },
    coinPositions: [
      { x: 1, y: 1 }
    ],
    turn: 1
  };

  it('renders grid with correct number of cells', () => {
    render(<GameBoard gameState={mockGameState} />);
    // Find the game grid using the test ID
    const gridCells = screen.getAllByTestId(/^grid-cell-/);
    expect(gridCells.length).toBe(4); // 2x2 grid
  });

  it('displays unit in correct position in flat view', () => {
    render(<GameBoard gameState={mockGameState} />);
    // Find the cell at position 0,0 which should contain unit A
    const unitCell = screen.getByTestId('grid-cell-0-0');
    expect(unitCell.textContent).toBe('A');
    expect(unitCell.dataset.cellType).toBe('unit');
  });

  it('displays coin in correct position', () => {
    render(<GameBoard gameState={mockGameState} />);
    // Find the cell at position 1,1 which should contain a coin
    const coinCell = screen.getByTestId('grid-cell-1-1');
    expect(coinCell.textContent).toBe('c');
    expect(coinCell.dataset.cellType).toBe('coin');
  });
  
  it('toggles between flat and isometric view', () => {
    render(<GameBoard gameState={mockGameState} />);
    
    // Initially in flat view
    expect(screen.getByTestId('game-grid')).not.toHaveStyle('transform: rotateX(60deg) rotateZ(45deg)');
    
    // Find and click the view toggle button
    const viewToggleButton = screen.getByRole('button', {
      name: /switch to isometric view/i,
    });
    fireEvent.click(viewToggleButton);
    
    // Now should be in isometric view
    expect(screen.getByTestId('game-grid')).toHaveStyle('transform: rotateX(60deg) rotateZ(45deg)');
    
    // Check that unit cell doesn't display text in isometric view
    // But the unit letter should still be visible in the floating label
    const unitCell = screen.getByTestId('grid-cell-0-0');
    expect(unitCell.textContent).toBe('');
    expect(screen.getAllByText('A')).toHaveLength(1); // Unit name should be in the floating label
  });
});
