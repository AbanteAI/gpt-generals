import React from 'react';
import { Box } from '@mui/material';
import { GameState, TerrainType } from '../models';

interface GameBoardProps {
  gameState: GameState;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  const { mapGrid, units, coinPositions } = gameState;
  
  // Calculate grid dimensions
  const gridHeight = mapGrid.length;
  const gridWidth = gridHeight > 0 ? mapGrid[0].length : 0;
  
  const isUnitAtPosition = (x: number, y: number): string | null => {
    for (const unitKey in units) {
      const unit = units[unitKey];
      if (unit.position.x === x && unit.position.y === y) {
        return unit.name;
      }
    }
    return null;
  };
  
  const isCoinAtPosition = (x: number, y: number): boolean => {
    return coinPositions.some(pos => pos.x === x && pos.y === y);
  };
  
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Box
        data-testid="game-grid"
        sx={{
          display: 'grid',
          gridTemplateColumns: `repeat(${gridWidth}, 30px)`,
          gridTemplateRows: `repeat(${gridHeight}, 30px)`,
          gap: '2px',
          backgroundColor: '#ccc',
          padding: '2px',
          border: '1px solid #999',
        }}
      >
        {mapGrid.map((row, y) => (
          // Use React Fragment as a container for each row to maintain grid structure
          <React.Fragment key={`row-${y}`}>
            {row.map((cell, x) => {
              const unitName = isUnitAtPosition(x, y);
              const hasCoin = isCoinAtPosition(x, y);
              
              return (
                <Box
                  key={`${x}-${y}`}
                  data-testid={`grid-cell-${x}-${y}`}
                  data-cell-type={unitName ? 'unit' : (hasCoin ? 'coin' : 'terrain')}
                  sx={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: cell === TerrainType.LAND ? '#8BC34A' : '#2196F3',
                    ...(unitName && { backgroundColor: '#F44336' }),
                    ...(hasCoin && { backgroundColor: '#FFC107' }),
                    fontWeight: 'bold',
                    color: unitName ? '#fff' : (hasCoin ? '#000' : undefined),
                  }}
                >
                  {unitName || (hasCoin ? 'c' : '')}
                </Box>
              );
            })}
          </React.Fragment>
        ))}
      </Box>
    </Box>
  );
};
