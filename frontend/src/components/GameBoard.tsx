import React from 'react';
import { Box, Grid } from '@mui/material';
import { GameState, TerrainType } from '../models';

interface GameBoardProps {
  gameState: GameState;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  const { mapGrid, units, coinPositions } = gameState;
  
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
      <Grid container spacing={0.5} sx={{ maxWidth: 'fit-content' }}>
        {mapGrid.map((row, y) => (
          row.map((cell, x) => {
            const unitName = isUnitAtPosition(x, y);
            const hasCoin = isCoinAtPosition(x, y);
            
            return (
              <Grid item key={`${x}-${y}`}>
                <Box
                  sx={{
                    width: 30,
                    height: 30,
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
              </Grid>
            );
          })
        ))}
      </Grid>
    </Box>
  );
};
