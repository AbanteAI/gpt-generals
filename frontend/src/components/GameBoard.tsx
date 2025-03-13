import React, { useState, useEffect } from 'react';
import { Box, IconButton, Paper, Grid, Typography } from '@mui/material';
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
  const [terrainCounts, setTerrainCounts] = useState({ land: 0, water: 0 });
  
  // Calculate grid dimensions
  const gridHeight = mapGrid.length;
  const gridWidth = gridHeight > 0 ? mapGrid[0].length : 0;
  
  // Count terrain types for debugging
  useEffect(() => {
    if (mapGrid.length > 0) {
      let land = 0;
      let water = 0;
      mapGrid.forEach(row => {
        row.forEach(cell => {
          if (cell === TerrainType.LAND) {
            land++;
          } else if (cell === TerrainType.WATER) {
            water++;
          }
        });
      });
      setTerrainCounts({ land, water });
    }
  }, [mapGrid]);
  
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

  // Get color for terrain
  const getTerrainColor = (cell: TerrainType) => {
    return cell === TerrainType.WATER ? '#0077BE' : '#8BC34A';
  };
  
  // Create a reversed copy of the map grid to display rows from bottom to top
  const reversedMapGrid = [...mapGrid].reverse();
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
      {/* Debug info */}
      <Typography variant="caption" color="text.secondary">
        Map contains: {terrainCounts.land} land, {terrainCounts.water} water tiles
      </Typography>
      
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
        {reversedMapGrid.map((row, reversedY) => {
          // Calculate the actual y position in the original grid
          const y = gridHeight - reversedY - 1;
          
          return (
            // Use React Fragment as a container for each row to maintain grid structure
            <React.Fragment key={`row-${y}`}>
              {row.map((cell, x) => {
                const unitName = isUnitAtPosition(x, y);
                const hasCoin = isCoinAtPosition(x, y);
                const isSelected = unitName && unitName === selectedUnit;
                const isWater = cell === TerrainType.WATER;
                
                // Determine the background color with priority: unit > coin > terrain
                let backgroundColor;
                if (unitName) {
                  backgroundColor = '#F44336'; // Red for units
                } else if (hasCoin) {
                  backgroundColor = '#FFC107'; // Yellow for coins
                } else {
                  backgroundColor = getTerrainColor(cell);
                }
                
                return (
                  <Box
                    key={`${x}-${y}`}
                    data-testid={`grid-cell-${x}-${y}`}
                    data-cell-type={unitName ? 'unit' : (hasCoin ? 'coin' : (isWater ? 'water' : 'land'))}
                    onClick={() => handleCellClick(x, y)}
                    sx={{
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor,
                      ...(isSelected && { 
                        border: '2px solid yellow',
                        boxSizing: 'border-box'
                      }),
                      fontWeight: 'bold',
                      color: unitName ? '#fff' : (hasCoin ? '#000' : undefined),
                      cursor: unitName ? 'pointer' : 'default',
                      // For water, add wave pattern
                      ...(isWater && !unitName && !hasCoin && {
                        backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                        backgroundSize: '10px 10px'
                      })
                    }}
                  >
                    {unitName || (hasCoin ? 'c' : (isWater ? '~' : ''))}
                  </Box>
                );
              })}
            </React.Fragment>
          );
        })}
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
