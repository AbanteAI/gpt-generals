import React, { useState } from 'react';
import { Box, IconButton, Paper, Grid } from '@mui/material';
import { GameState, TerrainType } from '../models';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { moveUnit } from '../api';

interface GameBoardProps {
  gameState: GameState;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  const { mapGrid, units, coinPositions } = gameState;
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  
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

  const handleCellClick = (x: number, y: number) => {
    const clickedUnit = isUnitAtPosition(x, y);
    if (clickedUnit) {
      setSelectedUnit(clickedUnit);
    }
  };

  const handleMoveUnit = async (direction: 'up' | 'down' | 'left' | 'right') => {
    if (selectedUnit) {
      await moveUnit(selectedUnit, direction);
    }
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
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
              const isSelected = unitName && unitName === selectedUnit;
              
              return (
                <Box
                  key={`${x}-${y}`}
                  data-testid={`grid-cell-${x}-${y}`}
                  data-cell-type={unitName ? 'unit' : (hasCoin ? 'coin' : 'terrain')}
                  onClick={() => handleCellClick(x, y)}
                  sx={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: cell === TerrainType.LAND ? '#8BC34A' : '#2196F3',
                    ...(unitName && { backgroundColor: '#F44336' }),
                    ...(hasCoin && { backgroundColor: '#FFC107' }),
                    ...(isSelected && { 
                      border: '2px solid yellow',
                      boxSizing: 'border-box'
                    }),
                    fontWeight: 'bold',
                    color: unitName ? '#fff' : (hasCoin ? '#000' : undefined),
                    cursor: unitName ? 'pointer' : 'default',
                  }}
                >
                  {unitName || (hasCoin ? 'c' : '')}
                </Box>
              );
            })}
          </React.Fragment>
        ))}
      </Box>

      {/* D-pad control */}
      <Paper elevation={3} sx={{ p: 2, width: 'fit-content' }}>
        <Grid container direction="column" alignItems="center" spacing={1}>
          <Grid item>
            <IconButton 
              color="primary" 
              onClick={() => handleMoveUnit('up')}
              disabled={!selectedUnit}
            >
              <ArrowUpwardIcon />
            </IconButton>
          </Grid>
          <Grid item container justifyContent="center" spacing={1}>
            <Grid item>
              <IconButton 
                color="primary" 
                onClick={() => handleMoveUnit('left')}
                disabled={!selectedUnit}
              >
                <ArrowBackIcon />
              </IconButton>
            </Grid>
            <Grid item>
              <IconButton 
                color="primary" 
                onClick={() => handleMoveUnit('down')}
                disabled={!selectedUnit}
              >
                <ArrowDownwardIcon />
              </IconButton>
            </Grid>
            <Grid item>
              <IconButton 
                color="primary" 
                onClick={() => handleMoveUnit('right')}
                disabled={!selectedUnit}
              >
                <ArrowForwardIcon />
              </IconButton>
            </Grid>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};
