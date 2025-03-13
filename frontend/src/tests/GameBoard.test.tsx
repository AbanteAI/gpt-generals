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
    const gridItems = container.querySelectorAll('.MuiGrid-item');
    expect(gridItems.length).toBe(4); // 2x2 grid
  });

  it('displays unit in correct position', () => {
    const { container } = render(<GameBoard gameState={mockGameState} />);
    const gridItems = container.querySelectorAll('.MuiGrid-item');
    const unitCell = gridItems[0];
    expect(unitCell.textContent).toBe('A');
  });

  it('displays coin in correct position', () => {
    const { container } = render(<GameBoard gameState={mockGameState} />);
    const gridItems = container.querySelectorAll('.MuiGrid-item');
    const coinCell = gridItems[3];
    expect(coinCell.textContent).toBe('c');
  });
});
