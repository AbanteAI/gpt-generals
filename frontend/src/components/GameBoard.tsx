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

// Large continuous water animation patterns
const waterWave = keyframes`
  0% { background-position: 0 0; }
  100% { background-position: 120px 60px; }
`;

const waterWave2 = keyframes`
  0% { background-position: 0 0; }
  100% { background-position: -80px 40px; }
`;

const waterRipple = keyframes`
  0% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0.5; }
  100% { transform: scale(1); opacity: 0.3; }
`;

const waterShimmer = keyframes`
  0% { opacity: 0.4; }
  50% { opacity: 0.7; }
  100% { opacity: 0.4; }
`;

const waterBubble = keyframes`
  0% { transform: translateY(0) scale(0.1); opacity: 0; }
  20% { opacity: 0.5; }
  80% { opacity: 0.5; }
  100% { transform: translateY(-8px) scale(0.3); opacity: 0; }
`;

// Define a global water pattern for the entire grid
const waterPattern = {
  position: 'absolute',
  content: '""',
  top: 0,
  left: 0,
  width: '200%',
  height: '200%',
  pointerEvents: 'none',
  zIndex: 0,
  transformOrigin: 'top left',
};

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
  
  // Create a water map to track connected water bodies
  const getWaterMap = () => {
    const waterTiles: {x: number, y: number}[] = [];
    
    // Find all water tiles
    mapGrid.forEach((row, y) => {
      row.forEach((cell, x) => {
        if (cell === TerrainType.WATER) {
          waterTiles.push({x, y});
        }
      });
    });
    
    return waterTiles;
  };
  
  // Get all water tiles for continuous pattern
  const waterTiles = getWaterMap();
  
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
  
  // Make sure grass/land tiles have no animation and are opaque
  const getLandStyle = (isWater: boolean) => {
    if (!isWater) {
      return {
        backgroundColor: '#8BC34A',
        // No animations or transparency
        opacity: 1,
        position: 'relative',
        zIndex: 1,
      };
    }
    return {};
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
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Water patterns are now handled individually by each water tile */}
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
                      ...(!isWater && !unitAtPos && !hasCoin ? getLandStyle(isWater) : { backgroundColor }),
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
                      
                      // Isometric view water enhancements with continuous flow effect
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'isometric' && {
                        position: 'relative',
                        overflow: 'hidden',
                        // Solid base color (not transparent)
                        backgroundColor: '#0088cc',
                        // First layer of water animation - large water pattern
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 40%), radial-gradient(circle at 70% 70%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 35%), radial-gradient(ellipse at 40% 60%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 50%)',
                          backgroundSize: '120px 120px, 80px 80px, 160px 120px',
                          // Position background based on tile coordinates for continuity
                          backgroundPosition: `calc(${x * 30}px) calc(${y * 30}px)`,
                          opacity: 0.7,
                          animation: `${waterWave} 20s infinite linear`,
                          zIndex: 1,
                        },
                        // Second layer - wave ripples
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(45deg, transparent 85%, rgba(255,255,255,0.3) 90%, transparent 95%), linear-gradient(135deg, transparent 85%, rgba(255,255,255,0.2) 90%, transparent 95%)',
                          backgroundSize: '60px 60px, 80px 80px',
                          // Position background based on tile coordinates for continuity
                          backgroundPosition: `calc(${x * 30}px) calc(${y * 30}px)`,
                          opacity: 0.6,
                          animation: `${waterWave2} 15s infinite linear`,
                          zIndex: 2,
                        },
                        // Create an additional div for highlights and bubbles
                        '&': {
                          position: 'relative',
                          '&:before': {
                            content: '""',
                            display: 'block',
                            position: 'absolute',
                            width: '100%',
                            height: '100%',
                            top: 0,
                            left: 0,
                            backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 70%)',
                            backgroundSize: '20px 20px',
                            opacity: 0.6,
                            animation: `${waterShimmer} 4s infinite ease-in-out`,
                            zIndex: 3,
                          },
                          // Add bubbles
                          '&:after': {
                            content: '""',
                            display: 'block',
                            position: 'absolute',
                            width: '3px',
                            height: '3px',
                            borderRadius: '50%',
                            backgroundColor: 'rgba(255, 255, 255, 0.4)',
                            // Randomize bubble positions using the tile coordinates
                            left: `${(x % 3) * 10 + 5}px`,
                            top: `${(y % 3) * 10 + 5}px`,
                            boxShadow: 'rgba(255, 255, 255, 0.3) 10px 5px 0px, rgba(255, 255, 255, 0.4) -5px 10px 0px',
                            // Randomize animation timing
                            animation: `${waterBubble} ${Math.floor(Math.random() * 4) + 6}s infinite ease-out ${Math.floor(Math.random() * 3)}s`,
                            zIndex: 4,
                          }
                        },
                      }),
                      
                      // Regular flat view water styling - with continuous effect
                      ...(isWater && !unitAtPos && !hasCoin && viewMode === 'flat' && {
                        position: 'relative',
                        overflow: 'hidden',
                        backgroundColor: '#0088cc', // Solid color, not transparent
                        // First layer - large wave pattern for continuity between tiles
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(45deg, rgba(255,255,255,0.3) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0.3) 75%, transparent 75%, transparent)',
                          backgroundSize: '40px 40px',
                          // Position background based on tile coordinates for continuity
                          backgroundPosition: `calc(${x * 30}px) calc(${y * 30}px)`,
                          opacity: 0.5,
                          animation: `${waterWave} 15s infinite linear`,
                          zIndex: 1,
                        },
                        // Second layer - finer wave pattern
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundImage: 'linear-gradient(-45deg, rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%, transparent)',
                          backgroundSize: '30px 30px',
                          // Position background based on tile coordinates for continuity
                          backgroundPosition: `calc(${x * 30}px) calc(${y * 30}px)`,
                          opacity: 0.4,
                          animation: `${waterWave2} 10s infinite linear`,
                          zIndex: 2,
                        },
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
