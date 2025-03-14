import React, { useState } from 'react';
import { Box, IconButton, Paper, Grid, Tooltip } from '@mui/material';
import { GameState, TerrainType } from '../models';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ViewInArIcon from '@mui/icons-material/ViewInAr';
import LanguageIcon from '@mui/icons-material/Language';
import { moveUnit } from '../api';
import { keyframes } from '@emotion/react';

// Define animations
const coinRotate = keyframes`
  0% { transform: rotateY(0deg); }
  100% { transform: rotateY(360deg); }
`;

const waterWave = keyframes`
  0% { background-position: 0 0; }
  50% { background-position: 10px 0; }
  100% { background-position: 0 0; }
`;

const robotHover = keyframes`
  0% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
  100% { transform: translateY(0); }
`;

const robotGlow = keyframes`
  0% { box-shadow: 0 0 5px 1px rgba(255, 255, 255, 0.3); }
  50% { box-shadow: 0 0 10px 3px rgba(255, 255, 255, 0.5); }
  100% { box-shadow: 0 0 5px 1px rgba(255, 255, 255, 0.3); }
`;

const labelPulse = keyframes`
  0% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(1); opacity: 0.9; }
`;

interface GameBoardProps {
  gameState: GameState;
}

interface UnitAtPosition {
  name: string;
  color: string;
}

export const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  const { mapGrid, units, players, coinPositions } = gameState;
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'flat' | 'isometric'>('flat');
  
  // Calculate grid dimensions
  const gridHeight = mapGrid.length;
  const gridWidth = gridHeight > 0 ? mapGrid[0].length : 0;
  
  const isUnitAtPosition = (x: number, y: number): UnitAtPosition | null => {
    for (const unitKey in units) {
      const unit = units[unitKey];
      if (unit.position.x === x && unit.position.y === y) {
        const playerColor = players?.[unit.player_id]?.color || '#F44336'; // Default to red
        return {
          name: unit.name,
          color: playerColor
        };
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
      setSelectedUnit(clickedUnit.name);
    }
  };

  const handleMoveUnit = async (direction: 'up' | 'down' | 'left' | 'right') => {
    if (selectedUnit) {
      await moveUnit(selectedUnit, direction);
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === 'flat' ? 'isometric' : 'flat');
  };

  // Get color for terrain
  const getTerrainColor = (cell: TerrainType) => {
    return cell === TerrainType.WATER ? '#0077BE' : '#8BC34A';
  };
  
  // Create a reversed copy of the map grid to display rows from bottom to top
  const reversedMapGrid = [...mapGrid].reverse();
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, position: 'relative' }}>
      {/* Container for both grid and floating labels */}
      <Box sx={{ position: 'relative' }}>
        {/* Floating labels for isometric view */}
        {viewMode === 'isometric' && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              zIndex: 100,
              pointerEvents: 'none', // Make sure clicks pass through to the grid
            }}
          >
            {Object.values(units).map((unit) => {
              const playerColor = players?.[unit.player_id]?.color || '#F44336';
              const isSelected = unit.name === selectedUnit;
              
              // Calculate position using isometric projection
              // For the correct isometric offset, we need to apply the same transform as the grid
              // but to the unit coordinates, then position them in screen space
              const cellSize = 30; // Size of each grid cell
              const gap = viewMode === 'isometric' ? 1 : 2; // Gap size matching the grid
              
              // The isometric projection formula:
              // screen_x = (grid_x - grid_y) * (cellSize/2) + offset
              // screen_y = (grid_x + grid_y) * (cellSize/4) + offset
              const isoX = (unit.position.x - unit.position.y) * (cellSize/2 + gap/2) + (gridWidth * cellSize / 2);
              const isoY = (unit.position.x + unit.position.y) * (cellSize/4 + gap/4) + 20;
              
              return (
                <Box
                  key={`label-${unit.name}`}
                  sx={{
                    position: 'absolute',
                    left: `${isoX}px`,
                    top: `${isoY - 35}px`, // Raise it above the unit
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}
                >
                  {/* Unit name badge */}
                  <Box
                    sx={{
                      width: '26px',
                      height: '26px',
                      borderRadius: '50%',
                      backgroundColor: 'white',
                      color: 'black',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '16px',
                      boxShadow: '0 0 8px rgba(0,0,0,0.6)',
                      border: `2px solid ${isSelected ? playerColor : 'black'}`,
                      animation: `${labelPulse} 2s infinite ease-in-out`,
                      // Apply a counter-rotation to keep the label upright
                      transform: 'rotateX(-60deg) rotateZ(-45deg)',
                    }}
                  >
                    {unit.name}
                  </Box>
                  
                  {/* Connecting arrow */}
                  <Box
                    sx={{
                      width: 0,
                      height: 0,
                      marginTop: '2px',
                      borderLeft: '6px solid transparent',
                      borderRight: '6px solid transparent',
                      borderTop: `10px solid ${isSelected ? playerColor : 'white'}`,
                      filter: 'drop-shadow(0 2px 2px rgba(0,0,0,0.5))',
                      // Match the counter-rotation
                      transform: 'rotateX(-60deg) rotateZ(-45deg)',
                    }}
                  />
                </Box>
              );
            })}
          </Box>
        )}
        
        {/* Game grid */}
        <Box
          data-testid="game-grid"
          sx={{
            display: 'grid',
            gridTemplateColumns: `repeat(${gridWidth}, 30px)`,
            gridTemplateRows: `repeat(${gridHeight}, 30px)`,
            gap: viewMode === 'isometric' ? '1px' : '2px',
            backgroundColor: '#ccc',
            padding: '2px',
            border: '1px solid #999',
            transformStyle: 'preserve-3d',
            transform: viewMode === 'isometric' ? 'rotateX(60deg) rotateZ(45deg)' : 'none',
            transformOrigin: 'center center',
            transition: 'transform 0.5s ease',
            perspective: '1000px',
            marginTop: viewMode === 'isometric' ? '50px' : '0',
          }}
        >
        {reversedMapGrid.map((row, reversedY) => {
          // Calculate the actual y position in the original grid
          const y = gridHeight - reversedY - 1;
          
          return (
            // Use React Fragment as a container for each row to maintain grid structure
            <React.Fragment key={`row-${y}`}>
              {row.map((cell, x) => {
                const unitAtPos = isUnitAtPosition(x, y);
                const hasCoin = isCoinAtPosition(x, y);
                const isSelected = unitAtPos && unitAtPos.name === selectedUnit;
                const isWater = cell === TerrainType.WATER;
                
                // Determine the background color with priority: unit > coin > terrain
                let backgroundColor;
                if (unitAtPos) {
                  backgroundColor = unitAtPos.color; // Use player's color for unit
                } else if (hasCoin) {
                  backgroundColor = '#FFC107'; // Yellow for coins
                } else {
                  backgroundColor = getTerrainColor(cell);
                }
                
                return (
                  <Box
                    key={`${x}-${y}`}
                    data-testid={`grid-cell-${x}-${y}`}
                    data-cell-type={unitAtPos ? 'unit' : (hasCoin ? 'coin' : (isWater ? 'water' : 'land'))}
                    onClick={() => handleCellClick(x, y)}
                    sx={{
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor,
                      ...(viewMode === 'isometric' && {
                        position: 'relative',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        transition: 'all 0.3s ease',
                        '::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: 'rgba(0,0,0,0.1)',
                          transform: 'translateZ(-5px) translateY(5px)',
                          zIndex: -1,
                        }
                      }),
                      ...(isSelected && { 
                        border: '2px solid yellow',
                        boxSizing: 'border-box'
                      }),
                      fontWeight: 'bold',
                      color: unitAtPos ? '#fff' : (hasCoin ? '#000' : undefined),
                      cursor: unitAtPos ? 'pointer' : 'default',
                      
                      // Isometric view enhancements
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'isometric' && {
                        animation: `${waterWave} 3s infinite linear`,
                        backgroundImage: 'linear-gradient(45deg, #0077BE 25%, #0099FF 50%, #0077BE 75%)',
                        backgroundSize: '20px 20px',
                      }),
                      
                      // Regular flat view water styling
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'flat' && {
                        backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                        backgroundSize: '10px 10px'
                      }),
                      
                      // Coin animations in isometric view
                      ...(hasCoin && viewMode === 'isometric' && {
                        animation: `${coinRotate} 2s infinite linear`,
                        borderRadius: '50%',
                        boxShadow: '0 0 5px rgba(255, 215, 0, 0.7)',
                        // Replace text 'c' with a circle
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          backgroundColor: '#FFD700',
                          border: '2px solid #B8860B',
                        }
                      }),
                      
                      // Simple but cool robot styling in isometric view
                      ...(unitAtPos && viewMode === 'isometric' && {
                        position: 'relative',
                        animation: `${robotHover} 2s infinite ease-in-out`,
                        // Main robot body
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '22px',
                          height: '22px',
                          top: '4px',
                          left: '4px',
                          borderRadius: '3px',
                          backgroundColor: unitAtPos.color,
                          border: '1px solid rgba(0,0,0,0.4)',
                          boxShadow: isSelected 
                            ? `0 0 10px 3px ${unitAtPos.color}` 
                            : '0 2px 4px rgba(0,0,0,0.3)',
                          zIndex: 1,
                          ...(isSelected && {
                            animation: `${robotGlow} 1.5s infinite ease-in-out`
                          })
                        },
                        // Robot eye visor
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '14px',
                          height: '4px',
                          borderRadius: '1px',
                          backgroundColor: 'rgba(255,255,255,0.9)',
                          boxShadow: '0 0 3px rgba(255,255,255,0.5)',
                          zIndex: 2,
                          top: '10px',
                          left: '8px'
                        }
                      })
                    }}
                  >
                    {/* Only show text labels in flat view */}
                    {viewMode === 'flat' && (unitAtPos ? unitAtPos.name : (hasCoin ? 'c' : ''))}
                  </Box>
                );
              })}
            </React.Fragment>
          );
        })}
        </Box>
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

      {/* View mode toggle button */}
      <Tooltip title={`Switch to ${viewMode === 'flat' ? 'isometric' : 'flat'} view`}>
        <IconButton 
          onClick={toggleViewMode}
          color="primary"
          sx={{ 
            position: 'fixed', 
            bottom: 16, 
            right: 16,
            backgroundColor: 'white',
            boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
            '&:hover': {
              backgroundColor: '#f5f5f5'
            }
          }}
        >
          {viewMode === 'flat' ? <ViewInArIcon /> : <LanguageIcon />}
        </IconButton>
      </Tooltip>
    </Box>
  );
};
