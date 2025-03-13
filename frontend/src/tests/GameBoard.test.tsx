import React from 'react';
import { render } from '@testing-library/react';
import { GameBoard } from '../components/GameBoard';
import { TerrainType } from '../models';

describe('GameBoard', () => {
  const mockGameState = {
    mapGrid: [
      [TerrainType.LAND, TerrainType.WATER],
      [TerrainType.WATER, TerrainType.LAND]
    ],
    units: {
      'A': { name: 'A', position: { x: 0, y: 0 } }
    },
    coinPositions: [
      { x: 1, y: 1 }
    ],
    turn: 1
  };

  it('renders grid with correct number of cells', () => {
    const { container } = render(<GameBoard gameState={mockGameState} />);
    // Find all direct children of the grid container (the cell elements)
    const gridContainer = container.querySelector('[style*="display: grid"]');
    const gridCells = gridContainer ? gridContainer.children : [];
    expect(gridCells.length).toBe(4); // 2x2 grid
  });

  it('displays unit in correct position', () => {
    const { container } = render(<GameBoard gameState={mockGameState} />);
    // Get all grid cells
    const gridContainer = container.querySelector('[style*="display: grid"]');
    const gridCells = Array.from(gridContainer?.children || []);
    // First cell should have unit A (position 0,0)
    const unitCell = gridCells[0];
    expect(unitCell.textContent).toBe('A');
  });

  it('displays coin in correct position', () => {
    const { container } = render(<GameBoard gameState={mockGameState} />);
    // Get all grid cells
    const gridContainer = container.querySelector('[style*="display: grid"]');
    const gridCells = Array.from(gridContainer?.children || []);
    // Last cell should have coin (position 1,1 is the 4th element in row-major order)
    const coinCell = gridCells[3];
    expect(coinCell.textContent).toBe('c');
  });
});
