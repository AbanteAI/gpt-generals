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

// Define animations for coin spinning on edge (like a coin on a table)
const coinRotate = keyframes`
  0% { transform: perspective(400px) rotateX(85deg) rotateY(0deg); }
  25% { transform: perspective(400px) rotateX(85deg) rotateY(90deg); }
  50% { transform: perspective(400px) rotateX(85deg) rotateY(180deg); }
  75% { transform: perspective(400px) rotateX(85deg) rotateY(270deg); }
  100% { transform: perspective(400px) rotateX(85deg) rotateY(360deg); }
`;

// Add a wobble animation to make the spinning more realistic
const coinWobble = keyframes`
  0% { transform: translateY(0) rotateX(85deg); }
  25% { transform: translateY(-1px) rotateX(80deg); }
  50% { transform: translateY(0) rotateX(85deg); }
  75% { transform: translateY(-1px) rotateX(90deg); }
  100% { transform: translateY(0) rotateX(85deg); }
`;

const coinShine = keyframes`
  0% { background-position: -50px -50px; }
  50% { background-position: 50px 50px; }
  100% { background-position: -50px -50px; }
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
                
                // Determine the background color with priority: unit > terrain (coins have custom styling)
                let backgroundColor;
                if (unitAtPos) {
                  backgroundColor = unitAtPos.color; // Use player's color for unit
                } else if (hasCoin) {
                  backgroundColor = viewMode === 'isometric' ? 'transparent' : getTerrainColor(cell); // Transparent in isometric, terrain in flat
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
                      color: unitAtPos ? '#fff' : undefined, // No text color for coins since we're using visual elements
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
                      
                      // Enhanced coin animations in isometric view
                      ...(hasCoin && viewMode === 'isometric' && {
                        position: 'relative',
                        zIndex: 10, // Make sure coin appears above the terrain
                        backgroundColor: 'transparent', // Make cell transparent to focus on the coin
                        
                        // The coin element with enhanced styling - spinning on edge
                        perspective: '800px',
                        transformStyle: 'preserve-3d',
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          background: 'linear-gradient(to right, #B8860B, #FFD700, #FFF7CC, #FFD700, #B8860B)',
                          backgroundSize: '200px 100%',
                          animation: `${coinRotate} 2.5s infinite linear, ${coinShine} 6s infinite linear, ${coinWobble} 1s infinite ease-in-out`,
                          boxShadow: '0 0 8px rgba(0,0,0,0.4)',
                          border: '1px solid #B8860B',
                          transformOrigin: 'center center',
                          transformStyle: 'preserve-3d',
                          left: 'calc(50% - 10px)',
                          top: 'calc(50% - 10px)',
                          backfaceVisibility: 'visible',
                        },
                        
                        // Add a shadow beneath to emphasize the coin spinning on the board
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '10px',
                          height: '4px',
                          borderRadius: '50%',
                          backgroundColor: 'rgba(0,0,0,0.4)',
                          filter: 'blur(1px)',
                          bottom: '2px',
                          left: 'calc(50% - 5px)', // Center the shadow
                          zIndex: 9,
                          animation: `${coinRotate} 2.5s infinite linear`,
                          transform: 'rotateX(0deg) rotateY(0deg)', // Keep shadow flat on the surface
                        }
                      }),
                      
                      // Unit styling in isometric view
                      ...(unitAtPos && viewMode === 'isometric' && {
                        animation: `${robotHover} 2s infinite ease-in-out`,
                        // Replace text with a robot shape
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          width: '20px',
                          height: '20px',
                          borderRadius: '2px',
                          backgroundColor: unitAtPos.color,
                          border: '1px solid rgba(0,0,0,0.3)',
                          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                          zIndex: 1,
                        },
                        // Robot eyes
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '10px',
                          height: '4px',
                          borderRadius: '1px',
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          zIndex: 2,
                          top: '8px',
                        }
                      }),
                      
                      // Enhanced flat view styling for coins
                      ...(hasCoin && viewMode === 'flat' && {
                        position: 'relative',
                        
                        // Create a visual coin in flat view too - spinning on edge
                        perspective: '800px',
                        transformStyle: 'preserve-3d',
                        
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          width: '20px',
                          height: '20px',
                          transform: 'translate(-50%, -50%)',
                          borderRadius: '50%',
                          background: 'linear-gradient(to right, #B8860B, #FFD700, #FFF7CC, #FFD700, #B8860B)',
                          boxShadow: '0 0 5px rgba(0,0,0,0.3)',
                          border: '1px solid #B8860B',
                          zIndex: 2,
                          animation: `${coinRotate} 2.5s infinite linear, ${coinWobble} 1s infinite ease-in-out`,
                          transformStyle: 'preserve-3d', 
                          transformOrigin: 'center center',
                          backfaceVisibility: 'visible',
                        },
                        
                        // Add shadow for flat view too
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '10px',
                          height: '3px',
                          top: 'calc(50% + 10px)',
                          left: 'calc(50% - 5px)',
                          borderRadius: '50%',
                          backgroundColor: 'rgba(0,0,0,0.3)',
                          filter: 'blur(1px)',
                          zIndex: 1,
                        }
                      })
                    }}
                  >
                    {/* Only show text labels for units in flat view */}
                    {viewMode === 'flat' && (unitAtPos ? unitAtPos.name : '')}
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
